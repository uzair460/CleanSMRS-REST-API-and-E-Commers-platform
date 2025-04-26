from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import UserRegistrationForm
from .tokens import account_activation_token
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import *
from django.http import HttpResponseRedirect

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Check if the email already exists
            email = form.cleaned_data['email']
            if get_user_model().objects.filter(email=email).exists():
                messages.error(request, "This email is already in use. Please use a different email address.")
                return redirect('register')  # Redirect back to register page

            user = form.save(commit=False)
            user.is_active = False  # Deactivate account until confirmed
            user.save()

            # Send the activation email
            send_activation_email(request, user, email)

            messages.success(request, "To compleate the registration Please check your email for an activation link")
            return redirect('login')  # Redirect to login page after registration
    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})

def send_activation_email(request, user, to_email):
    mail_subject = "Activate your account"
    message = render_to_string('template_activate_account.html', {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http',  # Use https if secure
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.send()



def activate(request, uidb64, token):
    try:
        # Decode the uidb64 to get the user ID
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)

        # Check if the token is valid
        if account_activation_token.check_token(user, token):
            user.is_active = True  # Activate the user account
            user.save()
            messages.success(request, "Your account has been activated successfully!")
            return redirect('login')  # Redirect to login page after successful activation
        else:
            messages.error(request, "The activation link is invalid or has expired.")
            return redirect('register')  # Redirect back to registration page if the token is invalid

    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        messages.error(request, "The activation link is invalid.")
        return redirect('register')  # Redirect back to registration page if there's an error


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('page1')  # Redirect to the page1 after successful login
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')

def homepage(request):
    products = Product.objects.all()  
    return render(request, 'home.html' , {'products': products})


from .models import Product  # Import the Product model
@login_required
def page1(request):
    # Query all products from the database
    products = Product.objects.all()  
    # Pass the products to the template
    return render(request, 'page1.html', {'products': products})



from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem, Product

def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    
    # Get or create the user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Add or update the product in the cart
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    # Redirect to the cart page after adding the product
    return redirect('cart')  # Ensure the cart page URL is named 'cart'


def cart(request):
    # Get the user's cart
    cart = Cart.objects.get(user=request.user)
    cart_items = cart.items.all()

    # Calculate total price for each item and overall cart price
    for item in cart_items:
        item.total_price = item.product.price * item.quantity

    total_cart_price = sum(item.total_price for item in cart_items)

    if request.method == "POST":
        # Collect address details from the form
        street_address = request.POST.get("street_address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        postal_code = request.POST.get("postal_code")
        country = request.POST.get("country")

        # Save address details in the session for use in the checkout session
        request.session['address'] = {
            'street_address': street_address,
            'city': city,
            'state': state,
            'postal_code': postal_code,
            'country': country
        }

        return redirect('create_checkout_session')

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_cart_price': total_cart_price,
    })

def remove_from_cart(request, item_id):
    cart_item = CartItem.objects.get(id=item_id)
    cart_item.delete()
    return redirect('cart')  # Redirect back to the cart page

def update_cart_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    if request.method == "POST":
        new_quantity = int(request.POST.get("quantity"))
        if new_quantity > 0:
            item.quantity = new_quantity
            item.save()
    return redirect('cart')

from django.shortcuts import redirect
from django.conf import settings
from django.http import JsonResponse
from .models import CartItem
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

YOUR_DOMAIN = "http://127.0.0.1:8000"

def create_checkout_session(request):
    try:
        cart_items = CartItem.objects.filter(cart__user=request.user)
        
        if not cart_items.exists():
            return JsonResponse({'error': 'No items in the cart to checkout.'})

        line_items = []
        for item in cart_items:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.product.name,
                        #'images': ['/myproject/media/static/images/'], 
                    },
                    'unit_amount': int(item.product.price * 100),  # Convert dollars to cents
                },
                'quantity': item.quantity,
            })

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/success/',
            cancel_url=YOUR_DOMAIN + '/page/',
        )

        # Save the checkout session ID for further reference
        request.session['checkout_session_id'] = checkout_session.id

        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
from .models import Order

import random
import string
from django.core.mail import send_mail
from django.conf import settings

def success_view(request):
    try:
        checkout_session_id = request.session.get('checkout_session_id')
        if not checkout_session_id:
            return redirect('cart')

        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()

        address = request.session.get('address')

        # Create an order
        order = Order.objects.create(
            user=request.user,
            cart=cart,
            total_amount=sum(item.product.price * item.quantity for item in cart_items),
            street_address=address['street_address'],
            city=address['city'],
            state=address['state'],
            postal_code=address['postal_code'],
            country=address['country'],
            status='completed',
        )


        from django.conf import settings


        # Check if any API product was purchased
        api_products = [item.product for item in cart_items if "API" in item.product.name]  # Customize the condition for API products
        if api_products:
            # Generate a random token
            token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

            # Save the generated token in the database
            api_token = API_token.objects.create(token=token)

            # Send an email with the token
            subject = "Your API Access Token"
            message = (
                f"Thank you for purchasing our API product!\n\n"
                f"Here is your access token: {token}\n\n"
                f"Please keep it secure and use it to access our API services.\n\n"
                f"Best regards,\nCleanSMRS"
            )
            recipient_email = request.user.email
            send_mail(subject, message, settings.EMAIL_HOST_USER, [recipient_email])

        # Clear the cart
        cart.items.all().delete()

        # Clear the session data
        del request.session['address']
        del request.session['checkout_session_id']

        return render(request, 'success.html', {'order': order})
    except Exception as e:
        return JsonResponse({'error': str(e)})


def cancel_view(request):
    return render(request, 'cancel.html')

def api_access_view(request):
    if request.method == "POST":
        # Get the token entered by the user
        entered_token = request.POST.get('token')
        
        # Check if the token exists in the database
        try:
            api_token = API_token.objects.get(token=entered_token)
            # Token is valid, grant access
            return HttpResponseRedirect('http://127.0.0.1:5000/docs')
        except API_token.DoesNotExist:
            # Token is invalid, show error message
            messages.error(request, "Invalid API token. Please try again.")
    
    return render(request, 'api_access_page.html')
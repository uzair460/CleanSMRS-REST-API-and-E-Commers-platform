from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [
    #admin
    path('admin/', admin.site.urls),

    #register
    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),

    #login
    path('login/', views.login, name='login'),

    #log out
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    #home page
    path('' , views.homepage),

    #e-commers page
    path('page/', views.page1 ,name='page1'),
    

    #cart
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update_quantity/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),

    #stripe/paymenth
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.success_view, name='success'),
    path('cancel/', views.cancel_view, name='cancel'),

    #api access page
    path('api-access/', views.api_access_view, name='api_access'),


]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
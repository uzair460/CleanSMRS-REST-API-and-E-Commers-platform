class Config:
    # Secret key for signing JWT tokens
    SECRET_KEY = 'your-secret-key'  # Change to your actual secret key

    # JWT token location (where to look for the token)
    JWT_TOKEN_LOCATION = ['headers']  # You can also use 'cookies' if needed

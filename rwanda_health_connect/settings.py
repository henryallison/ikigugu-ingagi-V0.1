from pathlib import Path

import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
import pymysql
pymysql.install_as_MySQLdb()
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Cloudinary settings
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', 'dom9oqh7m')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY', '383821267147834')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', 'jt-y0tV2EBV5eQGlQEPGV38ZsrU')
CLOUDINARY_UPLOAD_PRESET = 'rwanda_health_preset'  # Create this in your Cloudinary settings

# Add this to your settings.py
cloudinary.config(
  cloud_name = CLOUDINARY_CLOUD_NAME,
  api_key = CLOUDINARY_API_KEY,
  api_secret = CLOUDINARY_API_SECRET,
  secure = True
)

# Cloudinary Storage Settings
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
    'API_KEY': CLOUDINARY_API_KEY,
    'API_SECRET': CLOUDINARY_API_SECRET,
    'STATICFILES_MANIFEST_ROOT': os.path.join(BASE_DIR, 'manifest'),
    'SECURE': True
}
# Add these near the top with your other settings
SITE_URL = 'http://localhost:8000'  # Change to your production URL when deployed
SITE_NAME = 'Rwanda Health Connect'
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-wta1o+573pb9_wo!i09-sf04mrflc31kkzptegw)*6sy-65@9p'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'referral',
    'core',
    'accounts',
    'manage_hospital',
    'cloudinary',
    'cloudinary_storage',
    'patients',
    'find_hospital',
    
]
# Set default storage
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
# Custom User model
AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
     'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rwanda_health_connect.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'rwanda_health_connect.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Keep this engine, PyMySQL will be used behind the scenes
        'NAME': 'test',
        'USER': 'gWABC5QsgbZhuqA.root',
        'PASSWORD': 'fZXlW4bfrrswtg7Y',
        'HOST': 'gateway01.us-west-2.prod.aws.tidbcloud.com',
        'PORT': '4000',
        'OPTIONS': {
            'ssl': {
                'ca': os.path.join(BASE_DIR, 'certs', 'isrgrootx1.pem'), # Ensure this path is correct!
                # PyMySQL's SSL options might require string paths directly.
                # If you encounter issues, try:
                # 'ssl_ca': os.path.join(BASE_DIR, 'certs', 'isrgrootx1.pem'),
            }
            # For PyMySQL, charset might also be a useful option to explicitly set
            # 'charset': 'utf8mb4',
        },
        # Optional: Connection pooling (good for production)
        # 'CONN_MAX_AGE': 600, # seconds
    }
}

PWA_APP_NAME = 'Rwanda Health Connect'
PWA_APP_SHORT_NAME = 'RHC-APP'
PWA_APP_DESCRIPTION = "Health referal system"
PWA_APP_THEME_COLOR = '#000000'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'portrait'
PWA_APP_START_URL = '/'
PWA_APP_ICONS = [
    {
        'src': '/static/images/icon.jpg',
        'sizes': '160x160'
    }
]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]
# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/home/'  # Where users go after login
LOGOUT_REDIRECT_URL = '/accounts/login/'  # Where users go after logout

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Kigali'

USE_I18N = True

USE_TZ = True

# Add right after STATICFILES_DIRS
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # For collectstatic
STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticHashedCloudinaryStorage'  # Cloudinary for static files
from textbee import Client

api_key = os.getenv('TEXTBEE_API_KEY')
device_id = os.getenv('TEXTBEE_DEVICE_ID')

client = Client(api_key, device_id)

# settings.py
TEXTBEE_API_KEY = '9fb160b3-65aa-46ca-9c52-1ba4156e2fbd'  # Your API key
TEXTBEE_DEVICE_ID = '68262f69db6bef3de8cceb18'  # From TextBee dashboard


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# Static & media files
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # Global static files



# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

"""Django settings for the Applicant Tracking System (development only)."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Development-only settings. Production deployment is out of scope.
SECRET_KEY = "django-insecure-_o*1_%2qsx$7)g=cmoi1-u%6n1-_)36rhwfq)5=u(a4^560%0$"
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "django_tailwind_cli",
    "candidates",
    "jobs",
    "applications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Every view requires login unless marked @login_not_required.
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Authentication: every page requires login except login and password reset.
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "applications:dashboard"
LOGOUT_REDIRECT_URL = "login"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files. Tailwind (with DaisyUI) builds into assets/css/tailwind.css.
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "assets"]
TAILWIND_CLI_USE_DAISY_UI = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email: printed to the terminal during development (password reset).
MAILERS = {
    "default": {
        "BACKEND": "config.email.ReadableConsoleEmailBackend",
    },
}
DEFAULT_FROM_EMAIL = "ats@localhost"

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# BASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-change-this",
)

DEBUG = os.getenv(
    "DEBUG",
    "True",
).lower() in {
    "1",
    "true",
    "yes",
    "on",
}

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1,testserver",
).split(",")

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    "users.apps.UsersConfig",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "mozilla_django_oidc",

    "editor",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "mozilla_django_oidc.middleware.SessionRefresh",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "PhotoEditor.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND":
            "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",

                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",

                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = "PhotoEditor.wsgi.application"


# ============================================================
# DATABASES
# ============================================================

if os.getenv(
    "USE_POSTGRES",
    "False",
).lower() in {
    "1",
    "true",
    "yes",
    "on",
}:

    DATABASES = {
        "default": {
            "ENGINE":
                "django.db.backends.postgresql",

            "NAME":
                os.getenv(
                    "DB_NAME",
                    "photo_editor",
                ),

            "USER":
                os.getenv(
                    "DB_USER",
                    "postgres",
                ),

            "PASSWORD":
                os.getenv(
                    "DB_PASSWORD",
                    "postgres",
                ),

            "HOST":
                os.getenv(
                    "DB_HOST",
                    "localhost",
                ),

            "PORT":
                os.getenv(
                    "DB_PORT",
                    "5432",
                ),
        },

        "filestream": {
            "ENGINE":
                "mssql",

            "NAME":
                os.getenv(
                    "SQLSERVER_DB_NAME",
                    "Photo_editor_database",
                ),

            "USER":
                os.getenv(
                    "SQLSERVER_USER",
                    "",
                ),

            "PASSWORD":
                os.getenv(
                    "SQLSERVER_PASSWORD",
                    "",
                ),

            "HOST":
                os.getenv(
                    "SQLSERVER_HOST",
                    ".",
                ),

            "PORT":
                os.getenv(
                    "SQLSERVER_PORT",
                    "",
                ),

            "OPTIONS": {
                "driver":
                    os.getenv(
                        "SQLSERVER_DRIVER",
                        "ODBC Driver 18 for SQL Server",
                    ),

                "Encrypt":
                    "no",

                "TrustServerCertificate":
                    "yes",

                "extra_params":
                    "Trusted_Connection=Yes;"
                    "Encrypt=no;"
                    "TrustServerCertificate=yes;",
            },
        },
    }

else:

    DATABASES = {
        "default": {
            "ENGINE":
                "django.db.backends.sqlite3",

            "NAME":
                BASE_DIR / "db.sqlite3",
        },

        "filestream": {
            "ENGINE":
                "mssql",

            "NAME":
                os.getenv(
                    "SQLSERVER_DB_NAME",
                    "Photo_editor_database",
                ),

            "USER":
                os.getenv(
                    "SQLSERVER_USER",
                    "",
                ),

            "PASSWORD":
                os.getenv(
                    "SQLSERVER_PASSWORD",
                    "",
                ),

            "HOST":
                os.getenv(
                    "SQLSERVER_HOST",
                    ".",
                ),

            "PORT":
                os.getenv(
                    "SQLSERVER_PORT",
                    "",
                ),

            "OPTIONS": {
                "driver":
                    os.getenv(
                        "SQLSERVER_DRIVER",
                        "ODBC Driver 18 for SQL Server",
                    ),

                "Encrypt":
                    "no",

                "TrustServerCertificate":
                    "yes",

                "extra_params":
                    "Trusted_Connection=Yes;"
                    "Encrypt=no;"
                    "TrustServerCertificate=yes;",
            },
        },
    }


# ============================================================
# AUTHENTICATION
# ============================================================

AUTHENTICATION_BACKENDS = [
    "users.backends.KeycloakOIDCBackend",

    "django.contrib.auth.backends.ModelBackend",
]


# ============================================================
# KEYCLOAK / OPENID CONNECT
# ============================================================

OIDC_RP_CLIENT_ID = os.getenv(
    "OIDC_RP_CLIENT_ID",
    "",
)

OIDC_RP_CLIENT_SECRET = os.getenv(
    "OIDC_RP_CLIENT_SECRET",
    "",
)

OIDC_RP_SIGN_ALGO = os.getenv(
    "OIDC_RP_SIGN_ALGO",
    "RS256",
)


# ============================================================
# KEYCLOAK ISSUER
# ============================================================

OIDC_OP_ISSUER = os.getenv(
    "OIDC_OP_ISSUER",
    "http://localhost:8080/realms/imagedjango-dev",
)


# ============================================================
# KEYCLOAK AUTHORIZATION ENDPOINT
# ============================================================

OIDC_OP_AUTHORIZATION_ENDPOINT = os.getenv(
    "OIDC_OP_AUTHORIZATION_ENDPOINT",
    "http://localhost:8080/realms/imagedjango-dev/protocol/openid-connect/auth",
)


# ============================================================
# KEYCLOAK TOKEN ENDPOINT
# ============================================================

OIDC_OP_TOKEN_ENDPOINT = os.getenv(
    "OIDC_OP_TOKEN_ENDPOINT",
    "http://localhost:8080/realms/imagedjango-dev/protocol/openid-connect/token",
)


# ============================================================
# KEYCLOAK USERINFO ENDPOINT
# ============================================================

OIDC_OP_USER_ENDPOINT = os.getenv(
    "OIDC_OP_USER_ENDPOINT",
    "http://localhost:8080/realms/imagedjango-dev/protocol/openid-connect/userinfo",
)


# ============================================================
# KEYCLOAK JWKS ENDPOINT
# ============================================================

OIDC_OP_JWKS_ENDPOINT = os.getenv(
    "OIDC_OP_JWKS_ENDPOINT",
    "http://localhost:8080/realms/imagedjango-dev/protocol/openid-connect/certs",
)


# ============================================================
# KEYCLOAK LOGOUT ENDPOINT
# ============================================================

OIDC_OP_LOGOUT_ENDPOINT = os.getenv(
    "OIDC_OP_LOGOUT_ENDPOINT",
    "http://localhost:8080/realms/imagedjango-dev/protocol/openid-connect/logout",
)


# ============================================================
# OIDC CALLBACK
# ============================================================

OIDC_REDIRECT_URI = os.getenv(
    "OIDC_REDIRECT_URI",
    "http://localhost:8000/oidc/callback/",
)


# ============================================================
# USER CREATION
# ============================================================

OIDC_CREATE_USER = True


# ============================================================
# CLAIMS
# ============================================================

OIDC_USERNAME_CLAIM = "preferred_username"

OIDC_EMAIL_CLAIM = "email"

OIDC_FIRST_NAME_CLAIM = "given_name"

OIDC_LAST_NAME_CLAIM = "family_name"


# ============================================================
# SCOPES
# ============================================================

OIDC_RP_SCOPES = os.getenv(
    "OIDC_RP_SCOPES",
    "openid email profile",
)


# ============================================================
# OIDC SECURITY
# ============================================================

OIDC_USE_NONCE = True

OIDC_STORE_ID_TOKEN = True

OIDC_RENEW_ID_TOKEN_EXPIRY = True


# ============================================================
# IMPORTANT
# ============================================================
#
# DO NOT add:
#
# OIDC_AUTH_REQUEST_EXTRA_PARAMS = {
#     "prompt": "create",
# }
#
# That would affect NORMAL LOGIN as well.
#
# Registration uses:
#
# users.views.KeycloakRegistrationView
#
# which adds:
#
# prompt=create
#
# only to the registration request.
# ============================================================


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator",
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# ============================================================
# MEDIA
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = os.path.join(
    tempfile.gettempdir(),
    "MiniPhotoShopMedia",
)

os.makedirs(
    MEDIA_ROOT,
    exist_ok=True,
)


# ============================================================
# STORAGE
# ============================================================

STORAGES = {
    "default": {
        "BACKEND":
            "PhotoEditor.filestream_storage."
            "SqlServerFileStreamStorage",
    },

    "staticfiles": {
        "BACKEND":
            "django.contrib.staticfiles.storage."
            "StaticFilesStorage",
    },
}


# ============================================================
# SESSIONS
# ============================================================

SESSION_ENGINE = (
    "django.contrib.sessions.backends.db"
)

SESSION_COOKIE_AGE = 3600

SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# ============================================================
# LOGIN / LOGOUT
# ============================================================

LOGIN_REDIRECT_URL = "editor:index"

LOGIN_URL = "/users/login/"

LOGOUT_REDIRECT_URL = "/"


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)
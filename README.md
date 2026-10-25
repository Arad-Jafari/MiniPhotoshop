# MiniPhotoShop

MiniPhotoShop is a Django photo-editing application that uses OpenCV and NumPy to apply image effects. It includes a browser-based editor, Keycloak/OpenID Connect authentication, and a custom SQL Server FILESTREAM backend for image storage.

## Features

- Upload and preview JPG, JPEG, PNG, WEBP, and BMP images.
- Apply blur, Gaussian blur, median blur, sharpen, flip, rotate, resize, brightness, contrast, grayscale, and Gaussian noise effects.
- Remove effects from the editing history, reset to the original image, and download the current result.
- Sign in and register through a local Keycloak realm using OpenID Connect.

## Requirements

- Python 3.14 (matching the pinned dependencies in `requirements.txt`).
- Docker Compose, for the local Keycloak and PostgreSQL services.
- SQL Server with FILESTREAM enabled and a compatible `Media` table, plus the Microsoft ODBC Driver 18 for SQL Server. The configured media storage backend requires SQL Server when saving or loading images. Django migrations do not provision this table.

The Django relational database defaults to SQLite. PostgreSQL can be configured separately for Django, but the PostgreSQL service in `docker-compose.yml` is used by Keycloak.

## Local setup

1. Create and activate a virtual environment, then install the Python dependencies:

   ```powershell
   py -3.14 -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

   On macOS/Linux, activate with `source .venv/bin/activate`.

2. Create your local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

   If `.env` already exists, merge in the Keycloak variables from `.env.example` instead of replacing your local file. Update the `SQLSERVER_*` values to point to your FILESTREAM-enabled SQL Server. The example uses a placeholder OIDC client secret; for local testing, it must match the `secret` value in `keycloak/django-dev-realm.json`. Set a unique Django `SECRET_KEY` for your own environment.

3. Start Keycloak and its PostgreSQL database:

   ```powershell
   docker compose up -d
   ```

   Compose imports the development realm from `keycloak/django-dev-realm.json`. Keycloak is available at `http://localhost:8080`.

4. Apply Django migrations and create an administrator if needed:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. Start the development server:

   ```powershell
   python manage.py runserver
   ```

   Open `http://localhost:8000`. Use the application's sign-in or registration links to authenticate through Keycloak.

## Configuration notes

- `.env` is local-only and ignored by Git. Never commit real credentials, database files, uploads, or generated static files.
- The bundled Keycloak realm is for local development only. Replace its placeholder client secret and the local Compose passwords before use outside a private development environment.
- `USE_POSTGRES=True` selects PostgreSQL for Django's relational database; configure `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` accordingly. It does not configure SQL Server FILESTREAM storage.
- `DEBUG=True`, the local HTTP OIDC URLs, and the Compose Keycloak configuration are not production settings. A production deployment needs secure secrets, HTTPS, production-grade database and identity-provider configuration, and a proper Django deployment server.
- There is no license file yet. Publishing this repository publicly does not itself grant permission to reuse or redistribute its code; choose and add a license if you intend to do so.

## Project layout

```text
PhotoEditor/   Django project settings, URL configuration, and storage backend
editor/        Image editing views, processing, routes, and templates
users/         Login, registration, and OIDC integration
keycloak/      Development realm import configuration
static/        Static assets
```

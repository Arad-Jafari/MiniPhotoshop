from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from editor.views import serve_media


urlpatterns = [

    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "oidc/",
        include("mozilla_django_oidc.urls")
    ),

    path(
        "media/<path:media_path>",
        serve_media,
        name="serve_media"
    ),

    path(
        "",
        include(
            "editor.urls",
            namespace="editor"
        )
    ),

    path(
        "users/",
        include("users.urls")
    ),

]


if settings.DEBUG:

    static_root = (
        settings.STATICFILES_DIRS[0]
        if settings.STATICFILES_DIRS
        else settings.STATIC_ROOT
    )

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=static_root
    )
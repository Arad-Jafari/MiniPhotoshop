from django.shortcuts import render

from mozilla_django_oidc.views import (
    OIDCAuthenticationRequestView,
)


def login_view(request):

    return render(
        request,
        "users/login.html"
    )


def register(request):

    return render(
        request,
        "users/register.html"
    )


class KeycloakRegistrationView(
    OIDCAuthenticationRequestView
):

    def get_extra_params(self, request):

        params = super().get_extra_params(request)

        params["prompt"] = "create"

        return params


def register_start(request):

    return KeycloakRegistrationView.as_view()(request)
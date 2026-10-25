from django.urls import path

from . import views


urlpatterns = [

    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "register/",
        views.register,
        name="register",
    ),

    path(
        "register/start/",
        views.register_start,
        name="register_start",
    ),

]
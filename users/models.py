from django.conf import settings
from django.db import models


class KeycloakUserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='keycloak_profile')
    keycloak_sub = models.CharField(max_length=255, blank=True, null=True, unique=True)
    keycloak_username = models.CharField(max_length=150, blank=True, null=True)
    keycloak_email = models.EmailField(blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    claims = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} ({self.keycloak_sub or "no keycloak id"})'

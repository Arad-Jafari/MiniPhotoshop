from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import KeycloakUserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_keycloak_user_profile(sender, instance, created, **kwargs):
    if created:
        KeycloakUserProfile.objects.get_or_create(user=instance)

from django.contrib.auth import get_user_model
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


User = get_user_model()


class KeycloakOIDCBackend(OIDCAuthenticationBackend):

    def create_user(self, claims):

        username = (
            claims.get("preferred_username")
            or claims.get("email")
            or "unknown-user"
        )

        email = claims.get("email") or ""

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=claims.get("given_name", ""),
            last_name=claims.get("family_name", ""),
        )

        self._sync_profile(user, claims)

        return user


    def update_user(self, user, claims):

        user.username = (
            claims.get("preferred_username")
            or user.username
        )

        user.email = (
            claims.get("email")
            or user.email
        )

        user.first_name = (
            claims.get("given_name")
            or user.first_name
        )

        user.last_name = (
            claims.get("family_name")
            or user.last_name
        )

        user.save()

        self._sync_profile(user, claims)

        return user


    def filter_users_by_claims(self, claims):

        username = claims.get("preferred_username")

        if username:
            return User.objects.filter(
                username=username
            )


        email = claims.get("email")

        if email:
            return User.objects.filter(
                email=email
            )


        sub = claims.get("sub")

        if sub:

            profile = self._get_profile_for_sub(sub)

            if profile:
                return User.objects.filter(
                    pk=profile.user_id
                )


        return User.objects.none()


    def get_username(self, claims):

        return (
            claims.get("preferred_username")
            or claims.get("email")
            or "unknown-user"
        )


    def _sync_profile(self, user, claims):

        from .models import KeycloakUserProfile

        profile, _ = (
            KeycloakUserProfile.objects.get_or_create(
                user=user
            )
        )

        profile.keycloak_sub = claims.get("sub")

        profile.keycloak_username = (
            claims.get("preferred_username")
        )

        profile.keycloak_email = (
            claims.get("email")
        )

        profile.first_name = (
            claims.get("given_name", "")
        )

        profile.last_name = (
            claims.get("family_name", "")
        )

        profile.claims = claims

        profile.save()


    @staticmethod
    def _get_profile_for_sub(sub):

        from .models import KeycloakUserProfile

        try:

            return KeycloakUserProfile.objects.get(
                keycloak_sub=sub
            )

        except KeycloakUserProfile.DoesNotExist:

            return None
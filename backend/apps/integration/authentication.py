"""Token-based authentication for HRIS integration endpoints."""
import ipaddress
import logging

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import IntegrationToken

logger = logging.getLogger(__name__)


class IntegrationTokenAuthentication(BaseAuthentication):
    """
    Authenticate external HRIS systems via integration tokens.
    Token is passed in the Authorization header: 'Token <token_value>'
    Supports IP allowlisting and expiration.
    """

    keyword = "Token"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith(f"{self.keyword} "):
            return None

        token_value = auth_header[len(f"{self.keyword} "):]
        if not token_value:
            return None

        try:
            token = IntegrationToken.objects.select_related("tenant").get(
                token=token_value,
                is_active=True,
                is_deleted=False,
            )
        except IntegrationToken.DoesNotExist:
            raise AuthenticationFailed("Invalid or inactive integration token.")

        # Check expiration
        if token.expires_at and token.expires_at < timezone.now():
            raise AuthenticationFailed("Integration token has expired.")

        # Check IP allowlist
        client_ip = self._get_client_ip(request)
        if token.allowed_ips and not self._ip_allowed(client_ip, token.allowed_ips):
            logger.warning(
                "Integration token %s used from disallowed IP %s",
                token.name, client_ip,
            )
            raise AuthenticationFailed("Request from disallowed IP address.")

        # Update last used
        token.last_used_at = timezone.now()
        token.save(update_fields=["last_used_at"])

        # Set tenant on request
        request.tenant = token.tenant
        request.integration_token = token

        return (None, token)

    def _get_client_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

    def _ip_allowed(self, client_ip, allowed_ips):
        """Check if client IP is in the allowlist (supports CIDR notation)."""
        try:
            addr = ipaddress.ip_address(client_ip)
            for allowed in allowed_ips:
                try:
                    if "/" in allowed:
                        if addr in ipaddress.ip_network(allowed, strict=False):
                            return True
                    elif client_ip == allowed:
                        return True
                except ValueError:
                    continue
            return False
        except ValueError:
            return False

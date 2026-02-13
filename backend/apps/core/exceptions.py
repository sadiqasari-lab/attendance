"""Custom exception handling for consistent API responses."""
import logging

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    view = context.get("view")
    request = context.get("request")

    if response is not None:
        if response.status_code >= 500:
            logger.error(
                "Server error in %s: %s",
                view.__class__.__name__ if view else "unknown",
                exc,
                exc_info=True,
                extra={
                    "status_code": response.status_code,
                    "user": getattr(request, "user", None),
                    "path": getattr(request, "path", None),
                },
            )
        elif response.status_code >= 400:
            logger.warning(
                "Client error %d in %s: %s",
                response.status_code,
                view.__class__.__name__ if view else "unknown",
                exc,
                extra={"path": getattr(request, "path", None)},
            )

        response.data = {
            "success": False,
            "error": {
                "code": response.status_code,
                "detail": response.data,
            },
        }
    else:
        # Unhandled exception — log at critical level
        logger.critical(
            "Unhandled exception in %s: %s",
            view.__class__.__name__ if view else "unknown",
            exc,
            exc_info=True,
        )

    return response


class AttendanceValidationError(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Attendance validation failed."
    default_code = "attendance_validation_error"


class BiometricError(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Biometric verification failed."
    default_code = "biometric_error"


class DeviceNotRegisteredError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Device is not registered for this user."
    default_code = "device_not_registered"


class TenantAccessDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have access to this tenant."
    default_code = "tenant_access_denied"


class OfflineLimitExceeded(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Offline attendance limit exceeded for this shift."
    default_code = "offline_limit_exceeded"

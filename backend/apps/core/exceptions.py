"""Custom exception handling for consistent API responses."""
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "success": False,
            "error": {
                "code": response.status_code,
                "detail": response.data,
            },
        }
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

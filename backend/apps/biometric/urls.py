"""URL patterns for the biometric app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("templates", views.BiometricTemplateViewSet, basename="biometric-template")
router.register("enrollment-logs", views.BiometricEnrollmentLogViewSet, basename="enrollment-log")

urlpatterns = [
    path("enroll/", views.BiometricEnrollView.as_view(), name="biometric-enroll"),
    path("verify/", views.BiometricVerifyView.as_view(), name="biometric-verify"),
    path(
        "<uuid:employee_id>/revoke/",
        views.BiometricRevokeView.as_view(),
        name="biometric-revoke",
    ),
    path(
        "<uuid:employee_id>/delete/",
        views.BiometricDeleteView.as_view(),
        name="biometric-delete",
    ),
    path("", include(router.urls)),
]

"""URL patterns for the devices app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("list", views.DeviceRegistryViewSet, basename="device")
router.register("change-requests", views.DeviceChangeRequestViewSet, basename="device-change")

urlpatterns = [
    path("register/", views.DeviceRegisterView.as_view(), name="device-register"),
    path("<uuid:device_id>/approve/", views.DeviceApproveView.as_view(), name="device-approve"),
    path("root-detection/", views.RootDetectionView.as_view(), name="root-detection"),
    path("", include(router.urls)),
]

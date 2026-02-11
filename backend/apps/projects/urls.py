"""URL configuration for the projects app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EmployeeProjectAssignmentViewSet, ProjectViewSet

app_name = "projects"

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(
    r"project-assignments",
    EmployeeProjectAssignmentViewSet,
    basename="project-assignment",
)

urlpatterns = [
    path("", include(router.urls)),
]

from django.urls import path

from .views import dashboard, health

app_name = "visualizer"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("health/", health, name="health"),
]

from django.conf import settings
from django.shortcuts import render

from parser import parse_dataset

from .services import build_dashboard


def dashboard(request):
    parsed = parse_dataset(settings.BASE_DIR / "dataset")
    return render(request, "visualizer/dashboard.html", {"dashboard": build_dashboard(parsed)})

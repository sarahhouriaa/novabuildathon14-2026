from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

from parser import parse_dataset

from .services import build_dashboard


def dashboard(request):
    parsed = parse_dataset(settings.DATASET_ROOT)
    return render(request, "visualizer/dashboard.html", {"dashboard": build_dashboard(parsed)})


def health(request):
    return JsonResponse({"status": "ok"})

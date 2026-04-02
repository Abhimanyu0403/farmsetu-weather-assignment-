from django.http import JsonResponse
from django.shortcuts import render


def health(request):
    return JsonResponse({"status": "ok"})


def dashboard(request):
    return render(request, "climate/dashboard.html")

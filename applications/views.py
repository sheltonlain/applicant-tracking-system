from django.shortcuts import render


def dashboard(request):
    """Home page. A placeholder until the dashboard is built in Phase 11."""
    return render(request, "applications/dashboard.html")

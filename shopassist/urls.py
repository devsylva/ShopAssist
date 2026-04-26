from django.contrib import admin
from django.urls import path, include


def trigger_error(request):
    1 / 0


urlpatterns = [
    path('sentry-debug/', trigger_error),
    path('admin/', admin.site.urls),
    path('', include('agent.urls')),
]

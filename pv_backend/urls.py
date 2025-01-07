from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('pv_api.urls')),  # Include URLs from the pv_api application
]
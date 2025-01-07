from django.urls import path, include
from rest_framework import routers
from .views import PvDataViewSet

router = routers.DefaultRouter()
router.register(r'pvdata', PvDataViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
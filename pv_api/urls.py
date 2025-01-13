from django.urls import path, include
from rest_framework import routers
from .views import PvDataViewSet, PvMeasurementDataViewSet

router = routers.DefaultRouter()
router.register(r'pvdata', PvDataViewSet)
router.register(r'pvmeasurementdata', PvMeasurementDataViewSet) 

urlpatterns = [
    path('', include(router.urls)),
]
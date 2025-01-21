from django.urls import path, include
from rest_framework import routers
from .views import PvDataViewSet, PvMeasurementDataViewSet, ForecastDataDayAheadViewSet, ConfidenceApiView, LastNUniqueDataPointsView

router = routers.DefaultRouter()
router.register(r'pvdata', PvDataViewSet)
router.register(r'pvmeasurementdata', PvMeasurementDataViewSet) 
router.register(r'forecastdata', ForecastDataDayAheadViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('confidence/', ConfidenceApiView.as_view(), name='confidence'),  # Add the standalone APIView
    path('last-n-unique/', LastNUniqueDataPointsView.as_view(), name='last-n-unique'),
]
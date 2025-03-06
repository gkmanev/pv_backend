from django.urls import path, include
from rest_framework import routers
from .views import PvDataViewSet, PvMeasurementDataViewSet, ForecastDataDayAheadViewSet, ConfidenceApiView, LastNUniqueDataPointsView, PvTechnicalDataViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = routers.DefaultRouter()
router.register(r'pvdata', PvDataViewSet)
router.register(r'pvmeasurementdata', PvMeasurementDataViewSet) 
router.register(r'forecastdata', ForecastDataDayAheadViewSet)
router.register(r'pvtechnicaldata', PvTechnicalDataViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),    
    path('confidence/', ConfidenceApiView.as_view(), name='confidence'),  # Add the standalone APIView
    path('last-n-unique/', LastNUniqueDataPointsView.as_view(), name='last-n-unique'),
]
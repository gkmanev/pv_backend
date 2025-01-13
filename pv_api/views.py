from rest_framework import viewsets
from .models import PvTechnicalData, PvMeasurementData
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import PvDataSerializer, PvMeasurementDataSerializer
from pv_api.filters import PvMeasurementDataFilter  # <-- Import the filter

class PvDataViewSet(viewsets.ModelViewSet):
    queryset = PvTechnicalData.objects.all().order_by('signal_time')
    serializer_class = PvDataSerializer

class PvMeasurementDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PvMeasurementData.objects.all()
    serializer_class = PvMeasurementDataSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PvMeasurementDataFilter  # <-- Use the filter here

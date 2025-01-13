from rest_framework import viewsets
from .models import PvTechnicalData, PvMeasurementData
from .serializers import PvDataSerializer, PvMeasurementDataSerializer

class PvDataViewSet(viewsets.ModelViewSet):
    queryset = PvTechnicalData.objects.all().order_by('signal_time')
    serializer_class = PvDataSerializer

class PvMeasurementDataViewSet(viewsets.ModelViewSet):
    queryset = PvMeasurementData.objects.all().order_by('timestamp')
    serializer_class = PvMeasurementDataSerializer
    
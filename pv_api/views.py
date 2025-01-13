from rest_framework import viewsets
from .models import PvTechnicalData
from .serializers import PvDataSerializer

class PvDataViewSet(viewsets.ModelViewSet):
    queryset = PvTechnicalData.objects.all().order_by('signal_time')
    serializer_class = PvDataSerializer
from rest_framework import viewsets
from .models import PvData
from .serializers import PvDataSerializer

class PvDataViewSet(viewsets.ModelViewSet):
    queryset = PvData.objects.all().order_by('signal_time')
    serializer_class = PvDataSerializer
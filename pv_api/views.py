from rest_framework import viewsets
from .models import PvTechnicalData, PvMeasurementData
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta
from django.db.models import Max

from .serializers import PvDataSerializer, PvMeasurementDataSerializer
from pv_api.filters import PvMeasurementDataFilter  # <-- Import the filter

class PvDataViewSet(viewsets.ModelViewSet):
    queryset = PvTechnicalData.objects.all().order_by('signal_time')
    serializer_class = PvDataSerializer

class PvMeasurementDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PvMeasurementData.objects.all().order_by('timestamp')
    serializer_class = PvMeasurementDataSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PvMeasurementDataFilter 

    
    def get_queryset(self):
        """
        Override get_queryset to dynamically filter by the month of the most recent data point.
        """
        queryset = super().get_queryset()
        week = self.request.query_params.get('week')
        if week:
            # Get the most recent data point
            last_data_point = queryset.aggregate(Max('timestamp'))['timestamp__max']
            
            if last_data_point:
                # Get the first day of the month for the last data point
                last_data_point = last_data_point.replace(hour=0, minute=0, second=0, microsecond=0)
                # start_of_month = last_data_point.replace(day=1)  # First day of the last data point's month
                one_wee_ago = last_data_point - timedelta(days=7)
                
                # Filter the data to return only records from the current month
                queryset = queryset.filter(timestamp__gte=one_wee_ago)

        return queryset

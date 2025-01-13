from rest_framework import viewsets
from .models import PvTechnicalData, PvMeasurementData
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Max
from django.db.models.functions import TruncDay
from django.db.models import Sum
from datetime import timedelta

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
        aggregate_all = self.request.query_params.get('all')
        if aggregate_all:  # If 'all' query param is received
            queryset = (
                queryset.annotate(day=TruncDay('timestamp'))  # Truncate timestamps to the day
                .values('day')  # Group by truncated day
                .annotate(
                    total_production=Sum('production'),  # Aggregate production
                    avg_temperature=Sum('temperature_2m') / Sum('production'),  # Example: weighted avg temperature
                    total_uv_index=Sum('uv_index'),  # Aggregate UV index
                    total_radiation=Sum('direct_radiation')  # Aggregate direct radiation
                )
                .order_by('day')
            )

        return queryset

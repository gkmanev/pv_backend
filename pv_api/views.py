from rest_framework import viewsets
from .models import PvTechnicalData, PvMeasurementData, ForecastDataDayAhead
from django.db.models import Max
from django.db.models.functions import TruncDate
from django.db.models import Sum, Avg, F, Q
from datetime import datetime, timedelta
from .serializers import PvDataSerializer, PvMeasurementDataSerializer, AggregatedPvMeasurementDataSerializer, ForecastDataSerializer
from .pagination import CustomPageNumberPagination
from pv_api.tasks import task_min_max_intervals



class PvDataViewSet(viewsets.ModelViewSet):
    queryset = PvTechnicalData.objects.all().order_by('signal_time')
    serializer_class = PvDataSerializer

class PvMeasurementDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PvMeasurementData.objects.all().order_by('timestamp')
    serializer_class = PvMeasurementDataSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        aggregate_all = self.request.query_params.get('all')
        day_ahead = self.request.query_params.get('day_ahead')
        farm = self.request.query_params.get('farm')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if aggregate_all:
            queryset = (
                queryset.annotate(day=TruncDate('timestamp'))
                .values('day', 'farm')
                .annotate(
                    total_production=Sum('production'),
                    avg_temperature=Avg('temperature_2m', filter=~Q(temperature_2m=0)),
                    avg_uv_index=Avg('uv_index', filter=~Q(uv_index=0)),
                    avg_direct_radiation=Avg('direct_radiation', filter=~Q(direct_radiation=0)),
                    latitude=F('latitude'),
                    longitude=F('longitude')
                )
                .order_by('day', 'farm')
            )
        elif day_ahead:
            today = datetime.now().date()
            queryset = queryset.filter(timestamp__gte=today)

        elif start_date and end_date:
            task_min_max_intervals.delay(start_date)
            queryset = queryset.filter(timestamp__range=[start_date, end_date])

        if farm:
            queryset = queryset.filter(farm=farm)

        return queryset

    def get_serializer_class(self):
        if self.request.query_params.get('all'):
            return AggregatedPvMeasurementDataSerializer
        return self.serializer_class
    

class ForecastDataDayAheadViewSet(viewsets.ModelViewSet):
    queryset = ForecastDataDayAhead.objects.all().order_by('timestamp')
    serializer_class = ForecastDataSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset
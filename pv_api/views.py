from rest_framework import viewsets
from .models import PvTechnicalData, PvMeasurementData
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Max
from django.db.models.functions import TruncDate
from django.db.models import Sum, Avg, F, Q
from datetime import datetime, timedelta
from .serializers import PvDataSerializer, PvMeasurementDataSerializer, AggregatedPvMeasurementDataSerializer
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination



class PvDataViewSet(viewsets.ModelViewSet):
    queryset = PvTechnicalData.objects.all().order_by('signal_time')
    serializer_class = PvDataSerializer

class PvMeasurementDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PvMeasurementData.objects.all().order_by('timestamp')
    serializer_class = PvMeasurementDataSerializer
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """
        Override get_queryset to dynamically filter by the month of the most recent data point.
        """
        queryset = super().get_queryset()
        aggregate_all = self.request.query_params.get('all')
        day_ahead = self.request.query_params.get('day_ahead')
        farm = self.request.query_params.get('farm')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if aggregate_all:  # If 'all' query param is received            
            queryset = (
                queryset.annotate(day=TruncDate('timestamp'))  # Truncate to date instead of datetime
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
            if farm:
                queryset = queryset.filter(farm=farm)
        elif day_ahead:
            # Filter from today to the next day + 1 without aggregation
            # get today's date
            today = datetime.now().date()            
            queryset = queryset.filter(timestamp__gte=today)
        
        elif start_date and end_date and farm:
            # Filter by start_date, end_date and farm
            queryset = queryset.filter(timestamp__range=[start_date, end_date], farm=farm)
            

        else:
            queryset = queryset

        return queryset
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            if 'all' in request.query_params:
                serializer = AggregatedPvMeasurementDataSerializer(queryset, many=True)
            else:
                serializer = self.get_serializer(queryset, many=True)
            return self.get_paginated_response(serializer.data)    
            
        if 'all' in request.query_params:
            serializer = AggregatedPvMeasurementDataSerializer(queryset, many=True)
        else:
            serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import PvTechnicalData, PvMeasurementData, ForecastDataDayAhead
from django.db.models import Max
from django.db.models.functions import TruncDate
from django.db.models import Sum, Avg, F, Q
from datetime import datetime, timedelta
from .serializers import PvDataSerializer, PvMeasurementDataSerializer, AggregatedPvMeasurementDataSerializer, ForecastDataSerializer


class PvDataViewSet(viewsets.ModelViewSet):
    queryset = PvTechnicalData.objects.filter(parameter_id=720).order_by('timestamp')
    serializer_class = PvDataSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter data based on query parameters
        today = datetime.now().date()
        farm = self.request.query_params.get('farm')
        queryset = queryset.filter(timestamp__gte=today)  # Filter by today's data
        if farm:
            queryset = queryset.filter(installation_name=farm)  # Filter by farm name
        
        return queryset

    def list(self, request, *args, **kwargs):
        # Call the filtered queryset and pass it to the manager for resampling
        queryset = self.get_queryset()
        resampled_data = PvTechnicalData.resample.resample_to_15min(queryset)

        # Return the resampled data as a response
        return Response(resampled_data, status=status.HTTP_200_OK)    
   



class PvMeasurementDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PvMeasurementData.objects.all().order_by('timestamp')
    serializer_class = PvMeasurementDataSerializer    

    def get_queryset(self):
        queryset = super().get_queryset()
        aggregate_all = self.request.query_params.get('all')
        day_ahead = self.request.query_params.get('day-ahead')
        farm = self.request.query_params.get('farm')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        ppe = self.request.query_params.get('ppe')
        today_date = datetime.now().date()


        if farm:
            queryset = queryset.filter(farm=farm)
        if ppe:
            queryset = queryset.filter(ppe=ppe)
        if day_ahead:
            queryset = queryset.filter(timestamp__gte=today_date - timedelta(days=1))

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
            if start_date and end_date:
                queryset = queryset.filter(day__range=[start_date, end_date])
            elif start_date:
                queryset = queryset.filter(day__gte=start_date)            
                       
        
        elif start_date and end_date:         
            queryset = queryset.filter(timestamp__range=[start_date, end_date])      

        return queryset

    def get_serializer_class(self):
        if self.request.query_params.get('all'):
            return AggregatedPvMeasurementDataSerializer
        return self.serializer_class
    

class ConfidenceApiView(APIView):

    def get(self, request, *args, **kwargs):
        confidence = self.request.query_params.get('confidence')
        start_date = self.request.query_params.get('start_date')
        if confidence and start_date:
            PvMeasurementData.confidance.calculate_confidance(initial_date=datetime.strptime(start_date, "%Y-%m-%d"))
            return Response({"message": "Confidence intervals calculated and database updated."}, status=status.HTTP_200_OK)

class ForecastDataDayAheadViewSet(viewsets.ModelViewSet):
    queryset = ForecastDataDayAhead.objects.all().order_by('timestamp')
    serializer_class = ForecastDataSerializer
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset
    

class LastNUniqueDataPointsView(APIView):
    """
    Custom APIView to return data from the manager that produces a list.
    """
    def get(self, request, *args, **kwargs):
        # Use your custom manager
        unique_data = PvTechnicalData.unique_data.all() 
        serializer = PvDataSerializer(unique_data, many=True)
        return Response(serializer.data)
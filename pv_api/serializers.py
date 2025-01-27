from rest_framework import serializers
from .models import PvTechnicalData, PvMeasurementData, ForecastDataDayAhead

class PvDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PvTechnicalData
        fields = '__all__'

class PvMeasurementDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PvMeasurementData
        fields = '__all__'

class AggregatedPvMeasurementDataSerializer(serializers.Serializer):
    day = serializers.DateField()
    farm = serializers.CharField(max_length=100)  # Include `farm` if grouping by it
    total_production = serializers.DecimalField(max_digits=10, decimal_places=3)
    avg_temperature = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_uv_index = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_direct_radiation = serializers.DecimalField(max_digits=10, decimal_places=2)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=4)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=4)


class ForecastDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForecastDataDayAhead
        fields = '__all__'
        

class ResampledPvTechnicalDataSerializer(serializers.Serializer):
    rounded_timestamp = serializers.DateTimeField()
    parameter_id = serializers.IntegerField()
    installation_name = serializers.CharField(max_length=255)
    signal_value = serializers.FloatField()
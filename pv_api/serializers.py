from rest_framework import serializers
from .models import PvTechnicalData, PvMeasurementData

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
    total_production = serializers.DecimalField(max_digits=10, decimal_places=3)
    avg_temperature = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_uv_index = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_radiation = serializers.DecimalField(max_digits=10, decimal_places=2)
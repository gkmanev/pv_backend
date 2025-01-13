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
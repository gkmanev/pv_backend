from rest_framework import serializers
from .models import PvTechnicalData

class PvDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PvTechnicalData
        fields = '__all__'
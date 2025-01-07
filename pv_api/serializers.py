from rest_framework import serializers
from .models import PvData

class PvDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PvData
        fields = '__all__'
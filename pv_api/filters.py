# pv_api/filters.py

from django_filters import rest_framework as filters
from pv_api.models import PvMeasurementData

class PvMeasurementDataFilter(filters.FilterSet):
    farm = filters.CharFilter(field_name="farm", lookup_expr="icontains")
    start_date = filters.DateFilter(field_name="timestamp", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="timestamp", lookup_expr="lte")

    class Meta:
        model = PvMeasurementData
        fields = ['ppe', 'farm', 'start_date', 'end_date']

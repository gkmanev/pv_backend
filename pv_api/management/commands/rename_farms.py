from django.core.management.base import BaseCommand
from pv_api.models import PvMeasurementData, ForecastDataDayAhead
import json
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Import data from combined_weather_and_df_dam.csv into PvMeasurementData'

    def handle(self, *args, **kwargs):
        queryset = PvMeasurementData.objects.filter(timestamp__gte='2024-01-01', timestamp__lte='2024-03-31')
        project_mapping_path = os.path.join(settings.BASE_DIR, 'projects_mapping.json')
        project_mapping = []
        try:
            if os.path.exists(project_mapping_path):
                with open(project_mapping_path, 'r') as f:
                    project_mapping = json.load(f)
            else:
                print(f"Project mapping file not found: {project_mapping_path}")
                
        except Exception as e:
            print(f"Error loading project mapping file: {e}")

        update_data = []
        for data_point in queryset:
            for it in project_mapping:
                if data_point.ppe == it['PPE']:                             
                    # Rename data_point.installation_name to it['farm']
                    data_point.farm = it['farm']                    
                    update_data.append(data_point)

        PvMeasurementData.objects.bulk_update(update_data, ['farm'], batch_size=1000)
        print(f"{len(update_data)} data points updated.")

            

        



          
        
from django.core.management.base import BaseCommand
from pv_api.models import PvMeasurementData, ForecastDataDayAhead



class Command(BaseCommand):
    help = 'Import data from combined_weather_and_df_dam.csv into PvMeasurementData'

    def handle(self, *args, **kwargs):
        # Get the last item from farm Arcus from PvMeasurementData and get the date
        start_time = '2024-08-08T00:00:00Z'        
        end_time = '2024-08-10T00:00:00Z'        
        dam_item = PvMeasurementData.objects.filter(timestamp__gte=start_time, timestamp__lte=end_time)
        if dam_item.exists():
            for item in dam_item:                
                if not ForecastDataDayAhead.objects.filter(timestamp=item.timestamp, production_forecast=item.production).exists():
                    ForecastDataDayAhead.objects.create(
                        timestamp=item.timestamp,
                        production_forecast = item.production,
                        farm = item.farm,
                        ppe = item.ppe,
                    )



          
        
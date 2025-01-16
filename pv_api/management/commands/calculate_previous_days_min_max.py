
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from pv_api.models import PvMeasurementData, ForecastDataDayAhead
from django.db.models import Min, Max, Count
import pandas as pd

class Command(BaseCommand):
    help = 'Import data from combined_weather_and_df_dam.csv into PvMeasurementData'

    def handle(self, *args, **kwargs):        

        # Get the first item from ForecastData and get the date
        initial_date = '2024-08-08T00:00:00Z'
        # start_date = initial_date - timedelta(days=10)
        start_date = '2024-08-01T00:00:00Z'
        query = PvMeasurementData.objects.filter(timestamp__gte=start_date, timestamp__lte=initial_date)
        if query.exists():
            data = query.values('id', 'timestamp', 'production', 'farm', 'ppe')
            df = pd.DataFrame(data)
            
            # Check if DataFrame is empty
            if df.empty:
                self.stdout.write(self.style.WARNING("No data available."))
            else:
                # Convert timestamp to datetime and production to numeric
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['production'] = pd.to_numeric(df['production'])
                
                # Extract hour and minute part from timestamp
                df['time'] = df['timestamp'].dt.strftime('%H:%M')
                
                # Group by farm and time, calculate the min of production
                result_min = df.groupby(['farm', 'time'])['production'].min().reset_index()
                result_max = df.groupby(['farm', 'time'])['production'].max().reset_index()
                result = pd.merge(result_min, result_max, on=['farm', 'time'], suffixes=('_min', '_max'))  
                
                start_period = datetime.fromisoformat(initial_date.replace('Z', '+00:00'))
                end_period = start_period + timedelta(days=1)

                query_for_update_min_max = PvMeasurementData.objects.filter(timestamp__range=(start_period, end_period))
                if query_for_update_min_max.exists():
                    for _, row in result.iterrows():
                        # Get the corresponding ForecastDataDayAhead object
                        timestamp_str = f"{start_period.date()} {row['time']}:00"
                        timestamp = pd.to_datetime(timestamp_str)                        
                        obj, created = PvMeasurementData.objects.get_or_create(
                            timestamp=timestamp, farm=row['farm']
                        )
                        obj.min_production = row['production_min']
                        obj.max_production = row['production_max']

                        obj.save()

                    self.stdout.write(self.style.SUCCESS("DB Updated..."))


                






            


        



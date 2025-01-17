import requests
from .models import PvTechnicalData, PvMeasurementData
from datetime import timedelta
from datetime import datetime
import pandas as pd

def fetch_and_store_pv_data():
    url = "https://geos-api-app.azurewebsites.net/Api?ApiLogin=PV_API&ApiKey=19F1A3B8-27B9-4147-ACB1-5BC786E419D4"
    response = requests.get(url)
    data = response.json()    
    
    for item in data:
        signal_time = datetime.strptime(item['signal_time'], "%Y-%m-%d %H:%M:%S")
        for i in range(5):
            minute_signal_time = signal_time - timedelta(minutes=i)
            
            signal_value = float(item['signal_value']) / 5 if item['parameter_id'] == 720 else item['signal_value']
            
            # Check for uniqueness
            if not PvTechnicalData.objects.filter(installation_name=item['installation_name'], signal_time=minute_signal_time, parameter_id=item['parameter_id']).exists():
                PvTechnicalData.objects.create(
                    parameter_id=item['parameter_id'],
                    installation_name=item['installation_name'],
                    signal_uid=item['signal_uid'],
                    signal_time=minute_signal_time,
                    signal_value=signal_value,
                    unit=item['unit'],
                )
            else:
                # Handle the case where the record already exists
                print(f"Record with signal_time {minute_signal_time} and signal_uid {item['signal_uid']} already exists.")


def calculate_min_max_intervals(initial_date):
        
        # How many days you choose to calculate the confidance intervals
        start_date = initial_date - timedelta(days=8)    
        query = PvMeasurementData.objects.filter(timestamp__range=[start_date, initial_date])
        if query.exists():
            data = query.values('id', 'timestamp', 'production', 'farm', 'ppe')
            df = pd.DataFrame(data)            
            # Check if DataFrame is empty
            if df.empty:
                print("There are no data!")
            else:
                # Convert timestamp to datetime and production to numeric
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['production'] = pd.to_numeric(df['production'])
                
                # Extract hour and minute part from timestamp
                df['time'] = df['timestamp'].dt.strftime('%H:%M')
                
                # Group by farm and time, calculate the min of production
                result_min = df.groupby(['ppe', 'time'])['production'].min().reset_index()
                result_max = df.groupby(['ppe', 'time'])['production'].max().reset_index()
                result = pd.merge(result_min, result_max, on=['ppe', 'time'], suffixes=('_min', '_max'))  
                
                start_period = initial_date + timedelta(days=1)
                end_period = start_period + timedelta(days=1)

                query_for_update_min_max = PvMeasurementData.objects.filter(timestamp__range=(start_period, end_period))
                if query_for_update_min_max.exists():
                    for _, row in result.iterrows():
                        # Get the corresponding ForecastDataDayAhead object
                        timestamp_str = f"{start_period.date()} {row['time']}:00"
                        timestamp = pd.to_datetime(timestamp_str)                        
                        obj, created = PvMeasurementData.objects.get_or_create(
                            timestamp=timestamp, ppe=row['ppe']
                        )
                        obj.min_production = row['production_min']
                        obj.max_production = row['production_max']

                        obj.save() 

    
        
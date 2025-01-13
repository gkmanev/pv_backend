import requests
from .models import PvTechnicalData, PvMeasurementData
from datetime import timedelta
from datetime import datetime


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

def read_measurement_data_from_csv_and_update_db():
    # Read the measurement data from the CSV file combined_weather_and_df_dam.csv and update the PvMeasurementData table
    pass

    
        
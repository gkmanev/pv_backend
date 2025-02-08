import requests
from .models import PvTechnicalData, PvMeasurementData
from datetime import timedelta
from datetime import datetime
from .helper import SFTPDataProcessor, WeatherDataProcessor
import pandas as pd
import os
import json
from django.conf import settings

def fetch_and_store_pv_data():
    url = "https://geos-api-app.azurewebsites.net/Api?ApiLogin=PV_API&ApiKey=19F1A3B8-27B9-4147-ACB1-5BC786E419D4"
    response = requests.get(url)
    data = response.json()    
    
    for item in data:
        signal_time = datetime.strptime(item['signal_time'], "%Y-%m-%d %H:%M:%S")
        print(f"Resceived:{item['installation_name']}|| {item['signal_value']} ")
        for i in range(5):
            minute_signal_time = signal_time - timedelta(minutes=i)
            
            signal_value = float(item['signal_value']) / 5 if item['parameter_id'] == 720 else item['signal_value']
            
            # Check for uniqueness
            if not PvTechnicalData.objects.filter(installation_name=item['installation_name'], timestamp=minute_signal_time, parameter_id=item['parameter_id']).exists():
                PvTechnicalData.objects.create(
                    parameter_id=item['parameter_id'],
                    installation_name=item['installation_name'],
                    signal_uid=item['signal_uid'],
                    timestamp=minute_signal_time,
                    signal_value=signal_value,
                    unit=item['unit'],
                )
            else:
                # Handle the case where the record already exists
                print(f"Record with signal_time {minute_signal_time} and signal_uid {item['signal_uid']} already exists.")


def fetch_and_store_sftp_data():
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
    today = datetime.now().date()       
    seeking_date = today - timedelta(days=1)
    period = seeking_date - timedelta(days=4)
    while seeking_date > period:            
        for it in project_mapping:
                ppe = it.get("PPE", None)
                farm = it.get("farm", None)
                if ppe is not None:                                    
                    processor = SFTPDataProcessor(ppe, farm, seeking_date)
                    processor.process_data()          
        seeking_date -= timedelta(days=1)
        print("Data fetched and stored in the database.")


        
        
def fetch_and_store_weather_data_forecast():
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
    start = datetime.now().date() 
    #end = start + timedelta(days=1) 
    #start = datetime(2025, 1, 2).date()
    period = start - timedelta(days=3)
    #while start > period:      
    for it in project_mapping:
            ppe = it.get("PPE", None)
            lat = it.get("latitude", None)
            lon = it.get("longitude", None)
            if ppe is not None and lat is not None and lon is not None: 
                start_date = start 
                end_date = start
                # is_day_ahead_forecast = False and is_collect_history = False
                weather_data = WeatherDataProcessor(start_date, end_date, lat, lon, ppe, is_collect_history = False, is_day_ahead_forecast=True)
                weather_data.fetch_and_store_weather_data()
        #start -= timedelta(days=1)    
    print("Data fetched and stored in the database.")
    

def fetch_and_store_weather_data_historical():
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
    start = datetime.now().date() 
    #end = start + timedelta(days=1) 
    #start = datetime(2025, 1, 2).date()
    period = start - timedelta(days=3)
    while start > period:      
        for it in project_mapping:
            ppe = it.get("PPE", None)
            lat = it.get("latitude", None)
            lon = it.get("longitude", None)
            if ppe is not None and lat is not None and lon is not None: 
                start_date = start 
                end_date = start
                # is_day_ahead_forecast = False and is_collect_history = False
                weather_data = WeatherDataProcessor(start_date, end_date, lat, lon, ppe, is_collect_history = True, is_day_ahead_forecast=False)
                weather_data.fetch_and_store_weather_data()
        start -= timedelta(days=1)
    print("Data fetched and stored in the database.")
    

    

    
        
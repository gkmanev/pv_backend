

from django.core.management.base import BaseCommand
from pv_api.models import PvMeasurementData
import paramiko
from datetime import datetime, timedelta
import json
import os
from django.conf import settings
from pv_api.helper import WeatherDataProcessor



class Command(BaseCommand):
    help = 'Fetch data from SFTP and store it in the database'

    def handle(self, *args, **kwargs):
        
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
        while start > datetime(2025, 1, 31).date():       
            for it in project_mapping:
                ppe = it.get("PPE", None)
                lat = it.get("latitude", None)
                lon = it.get("longitude", None)
                if ppe is not None and lat is not None and lon is not None: 
                    start_date = start 
                    end_date = start
                    # is_day_ahead_forecast = False and is_collect_history = False
                    weather_data = WeatherDataProcessor(start_date, end_date, lat, lon, ppe, is_collect_history=True)
                    weather_data.fetch_and_store_weather_data()
            start -= timedelta(days=1)    
                         
            
        print("Data fetched and stored in the database.")


        
        

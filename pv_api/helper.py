from pv_api.models import PvMeasurementData
import paramiko
from datetime import datetime, timedelta
import json
import os
from django.conf import settings
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from pv_api.models import PvMeasurementData
import zipfile
import dropbox
import re
import xml.etree.ElementTree as ET


class SFTPDataProcessor:
    def __init__(self, ppe, farm, seeking_date):
        self.hostname = "skftp.enea.pl"
        self.port = 2222
        self.username = "gptp.urb"
        self.password = "Ju3D04dCJs"
        self.ppe = ppe
        self.farm = farm
        self.seeking_date = seeking_date
        self.create_placeholders_for_today_and_tomorrow()
        

    def create_placeholders_for_today_and_tomorrow(self):
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        for date in [today, tomorrow]:
            current_time = datetime.combine(date, datetime.min.time())
            while current_time < datetime.combine(date, datetime.max.time()):
                PvMeasurementData.objects.update_or_create(
                    timestamp=current_time,
                    ppe=self.ppe,
                    defaults={
                        'production': None,
                        'temperature_2m': 0,
                        'uv_index': 0,
                        'direct_radiation': 0,
                        'latitude': 0,
                        'longitude': 0,
                        'farm': self.farm
                    }
                )
                current_time += timedelta(minutes=15)


    def prepare_file_name(self):
        file_date_to_str = self.seeking_date.strftime("%Y%m%d")
        return f"ENED_{self.ppe}_LN01_COP_{file_date_to_str}.dat"
    
    def save_to_db(self, data_list):

        project_mapping_path = os.path.join(settings.BASE_DIR, 'projects_mapping.json')
        # Load the JSON file
        project_mapping = []
        try:
            if os.path.exists(project_mapping_path):
                with open(project_mapping_path, 'r') as f:
                    project_mapping = json.load(f)
            else:
                print(f"Project mapping file not found: {project_mapping_path}")
        except Exception as e:
            print(f"Error loading project mapping file: {e}")

        for it in project_mapping:
            found = it.get("PPE", None)
            if found == self.ppe:
                for data in data_list:
                    try:
                        timestamp = data['timestamp']
                        production = data['value']
                        latitude = it['latitude']
                        longitude = it['longitude']
                        farm = it['farm']
                        production = round(production, 2)                       
                        PvMeasurementData.objects.update_or_create(
                            timestamp=timestamp,
                            ppe=self.ppe,
                            defaults={
                            'production': production,
                            'latitude': latitude,
                            'longitude': longitude,   
                            'farm': farm,                
                            }
                        )
                    except Exception as e:
                        print(f"Error saving data to database: {e}")

    def prepare_data(self, fields): 
        interval_data = fields[6:] 
        interval_data = fields[6:len(fields) - 1]
        current_time = datetime.combine(self.seeking_date, datetime.min.time())
        processed_data = []
        for interval in interval_data:
            value, direction = interval
            processed_data.append({
                'timestamp': current_time,
                'value': float(value),
            })
            current_time += timedelta(minutes=15)
        self.save_to_db(processed_data)
    
    def find_and_read_file(self, sftp, remote_path, file_name):
        try:
            items = sftp.listdir_attr(remote_path)                
            for item in items:
                item_path = f"{remote_path}/{item.filename}"
                if item.st_mode & 0o40000:  
                    self.find_and_read_file(sftp, item_path, file_name)
                else:                                           
                    if item.filename == file_name:
                        print(f"File found: {item_path}")
                        with sftp.file(item_path, "r") as file:
                            file_fields = []
                            for line in file:
                                line = line if isinstance(line, str) else line.decode("utf-8")
                                fields = line.strip().split(",")  
                                file_fields.append(fields)
                            self.prepare_data(file_fields)
                            print("File processed and data stored")
                            return
        except Exception as e:
            print(f"Error accessing {remote_path}: {e}")
        
    
    def process_data(self):
        try:
            transport = paramiko.Transport((self.hostname, self.port))
            transport.connect(username=self.username, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            print(f"Searching for file '{self.prepare_file_name()}'...")
            self.find_and_read_file(sftp, '.', self.prepare_file_name())
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            sftp.close()
            transport.close()
            print("SFTP connection closed.")

        
class WeatherDataProcessor:
    def __init__(self, start_date, end_date, latitude, longitude, ppe, is_day_ahead_forecast = False, is_collect_history = False):
        self.cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        self.retry_session = retry(self.cache_session, retries = 5, backoff_factor = 0.2)
        self.openmeteo = openmeteo_requests.Client(session = self.retry_session)
        self.weather_list = []
        self.url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
        self.ppe = ppe
        self.latitude = latitude
        self.longitude = longitude
        self.start_date = start_date
        self.end_date = end_date
        self.is_day_ahead_forecast = is_day_ahead_forecast
        self.collect_history = is_collect_history
                
    
    def fetch_and_store_weather_data(self):
        params = {
		    "latitude": self.latitude,
		    "longitude": self.longitude,
		    "start_date": self.start_date,
		    "end_date": self.end_date,
		    "hourly": ["temperature_2m", "direct_radiation"]
	    }
        if self.collect_history:
            self.url = "https://archive-api.open-meteo.com/v1/archive"

        elif self.is_day_ahead_forecast:
            params = {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "hourly": ["temperature_2m", "direct_radiation"],
                "past_days": 2,
	            "forecast_days": 2
            }
            self.url = "https://api.open-meteo.com/v1/forecast"
        
        
          
        responses = self.openmeteo.weather_api(self.url, params=params)
        response = responses[0]
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        #hourly_uv_index = hourly.Variables(1).ValuesAsNumpy()
        hourly_direct_radiation = hourly.Variables(1).ValuesAsNumpy()
        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
	    )}
        
        # Check if hourly_temperature_2m is not empty
        if pd.isna(hourly_temperature_2m).all() or pd.isna(hourly_direct_radiation).all():
            print("No temperature and radiation data found")
        else:
            hourly_data["temperature_2m"] = hourly_temperature_2m       
            hourly_data["direct_radiation"] = hourly_direct_radiation
            hourly_dataframe = pd.DataFrame(data = hourly_data) 
            # remove if nans into hourly_dataframe
            hourly_dataframe = hourly_dataframe.dropna()              
            
            self.update_data_weather_fields(hourly_dataframe)          
        
        
    
    def update_data_weather_fields(self, hourly_dataframe):
        
        obj_to_update = []
        for index, row in hourly_dataframe.iterrows():
            timestamp_start = row['date']
            timestamp_end = timestamp_start + timedelta(hours=1)
            temperature_2m = round(row['temperature_2m'], 2)
            #uv_index = round(row['uv_index'], 2)
            direct_radiation = round(row['direct_radiation'],2)            
            queryset = PvMeasurementData.objects.filter(timestamp__range=[timestamp_start, timestamp_end], ppe=self.ppe)
            
            if queryset.exists():
                for obj in queryset:
                    obj.temperature_2m = temperature_2m
                    #obj.uv_index = uv_index                    
                    if self.collect_history:
                        obj.direct_radiation = direct_radiation
                        print(f"{timestamp_start} || {direct_radiation}")
                    else:                                       
                        obj.direct_radiation_forecast = direct_radiation                    
                    obj.latitude = self.latitude
                    obj.longitude = self.longitude
                    obj_to_update.append(obj)        
            else:
                print(f"No data found for timestamp {timestamp_start}")
        try:
            if self.collect_history:
                PvMeasurementData.objects.bulk_update(obj_to_update, ['temperature_2m', 'direct_radiation'])
            else:
                PvMeasurementData.objects.bulk_update(obj_to_update, ['temperature_2m', 'direct_radiation_forecast'])
        except Exception as e:
            print(f"Error updating weather data fields: {e}")


	    

class OneDriveDataProcessor:

       
    def __init__(self):      
        #self.dropbox_downloader()
        self.folder = 'test'  # You can make this dynamic if needed.
        self.ppe = None
        self.file_date = None
        

    def dropbox_downloader(self):
        dbx = dropbox.Dropbox(settings.DROPBOX_TOKEN)
        script_dir = settings.BASE_DIR
        local_test_dir = os.path.join(script_dir, self.folder)
        os.makedirs(local_test_dir, exist_ok=True)
        
        for entry in dbx.files_list_folder('').entries:
            if entry.name == self.folder:               
                for entry in dbx.files_list_folder(f'/{self.folder}').entries:
                    local_path = os.path.join(local_test_dir, f'{entry.name}')
                   
                    dbx.files_download_to_file(local_path, f'/{self.folder}/{entry.name}')


    def filter_the_ENED_files(self, file):
        # Define patterns for both kinds of file names
        patterns = [
            r'ENED_\d+_\w+_\w+_\d{8}',
            r'(\d+)_\d+_CO_(\d{8})\.dat'
        ]
        
        # Check if the file matches any of the patterns
        for pattern in patterns:
            if re.match(pattern, file) or file.endswith('.xml'):
                return file
        return None  # explicitly return None when no match


    def extract_downloaded_files(self):
        folder_path = os.path.join(os.getcwd(), self.folder)
        extracted_files = os.listdir(folder_path)
        # Extract the zipped
        for file in extracted_files:
            if file.endswith('.zip'):
                with zipfile.ZipFile(os.path.join(folder_path, file), 'r') as zip_ref:
                    zip_ref.extractall(folder_path)

       
    def filter_extracted_files_and_process_data(self):
        folder_path = os.path.join(os.getcwd(), self.folder)
        extracted_files = os.listdir(folder_path)    
        print(extracted_files)    
        for data in extracted_files:
            # List all files in the extracted folder recursively
            for root, dirs, files in os.walk(os.path.join(folder_path, data)):
                for file in files:            
                    filtered = self.filter_the_ENED_files(file)
                   
                    if filtered:                        
                        self.prepare_files(root, filtered)
                        
       
   
    def prepare_files(self, root, file): 
        if file.endswith('.xml'):
            full_path = os.path.join(root, file)            
            if not os.path.exists(full_path):  
                raise FileNotFoundError(f"File does not exist: {full_path}")
            xml_content = None
            with open(full_path, "r", encoding="utf-8") as f:
                xml_content = f.read()
            if xml_content:
                self.process_files_xml(xml_content)
        # else:
        #     file_fields = []       
        #     with open(os.path.join(root, file), 'r') as f:
        #         content = f.readlines()                      
        #         for line in content[6:]:                
        #             line = line if isinstance(line, str) else line.decode("utf-8")            
        #             fields = line.strip().split(",")  
        #             file_fields.append(fields)
        #         ppe, file_date = self.parse_file_name(file)
        #         if file_date and ppe:
        #             self.ppe = ppe
        #             self.file_date = file_date
        #             self.process_files(file_fields)
        #         else:
        #             print(f"Failed to parse the file name: {file}")            
                
    def process_files(self, fields):       
        interval_data = fields[6:] 
        interval_data = fields[6:len(fields) - 1]
        current_time = datetime.combine(self.file_date, datetime.min.time())
        processed_data = []
        for interval in interval_data:
            value, direction = interval
            processed_data.append({
                'timestamp': current_time,
                'value': float(value),
            })
            current_time += timedelta(minutes=15)  
        self.save_db(processed_data)     
          
            
    def parse_file_name(self, file):
        # Define patterns for both kinds of file names
        patterns = [
            r'ENED_(\d+)_\w+_\w+_(\d{8})',
            r'(\d+)_\d+_CO_(\d{8})\.dat'
        ]
        
        # Check if the file matches any of the patterns and extract information
        for pattern in patterns:
            match = re.search(pattern, file)
            if match:
                long_number = match.group(1)
                date_str = match.group(2)
                date = datetime.strptime(date_str, '%Y%m%d').date()
                return long_number, date
        return None, None
    
    
    def process_files_xml(self, xml_content):
        root = ET.fromstring(xml_content)        
        for ppe in root.findall(".//PPE"):
            kod_ppe = ppe.find("kodPPE").text
            self.ppe = kod_ppe
            er_data = []
            
            for er in ppe.findall("ER"):
                t = er.find("t").text            
                ewv = er.find("Ewv").text      
                ews = er.find("Ews").text
                er_data.append({
                    "ppe":kod_ppe,
                    "timestamp": t,
                    "value": ewv,  
                    "value_ews": ews                 
                })
            self.save_db(er_data)
            
          
    def save_db(self, data_list):
        
        project_mapping_path = os.path.join(settings.BASE_DIR, 'projects_mapping.json')
        # Load the JSON file
        project_mapping = []
        try:
            if os.path.exists(project_mapping_path):
                with open(project_mapping_path, 'r') as f:
                    project_mapping = json.load(f)
            else:
                print(f"Project mapping file not found: {project_mapping_path}")
        except Exception as e:
            print(f"Error loading project mapping file: {e}")

        for it in project_mapping:
            found = it.get("PPE", None)
            if found == self.ppe:                  
                    for data in data_list:
                        try:                        
                            timestamp = data['timestamp']
                            production = data['value']
                            latitude = it['latitude']
                            longitude = it['longitude']
                            farm = it['farm']
                            production = round(production, 2)    
                            print(f"PPE: {self.ppe} || Timestamp: {timestamp} || Production: {production}")                                    
                            # _, created = PvMeasurementData.objects.get_or_create(
                            # timestamp=timestamp,
                            # ppe=self.ppe,
                            # defaults={
                            #     'production': production,
                            #     'latitude': latitude,
                            #     'longitude': longitude,   
                            #     'farm': farm,                
                            #     }
                            # )
                        except Exception as e:
                            print(f"Error saving data to database: {e}")
            


# test = OneDriveDataProcessor()
# test.filter_extracted_files_and_process_data()


           
            
            


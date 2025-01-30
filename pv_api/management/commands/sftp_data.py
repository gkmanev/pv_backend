from django.core.management.base import BaseCommand
from pv_api.models import PvMeasurementData
import paramiko
from datetime import datetime, timedelta
import json
import os
from django.conf import settings
from pv_api.helper import SFTPDataProcessor



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
        today = datetime.now().date()       
        seeking_date = today - timedelta(days=1)
        while seeking_date > datetime(2025, 1, 26).date():            
            for it in project_mapping:
                    ppe = it.get("PPE", None)
                    farm = it.get("farm", None)
                    if ppe is not None:                                    
                        processor = SFTPDataProcessor(ppe, farm, seeking_date)
                        processor.process_data()          
            seeking_date -= timedelta(days=1)
        print("Data fetched and stored in the database.")


        
        

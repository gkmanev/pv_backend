import requests
from .models import PvData

def fetch_and_store_pv_data():
    url = "https://geos-api-app.azurewebsites.net/Api?ApiLogin=PV_API&ApiKey=19F1A3B8-27B9-4147-ACB1-5BC786E419D4"
    response = requests.get(url)
    data = response.json()
    print(data)
    for item in data:
        PvData.objects.update_or_create(
            signal_uid=item['signal_uid'],
            defaults={
                'parameter_id': item['parameter_id'],
                'installation_name': item['installation_name'],
                'signal_time': item['signal_time'],
                'signal_value': item['signal_value'],
                'unit': item['unit'],
            }
        )
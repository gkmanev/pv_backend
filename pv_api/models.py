from django.db import models
from datetime import datetime, timedelta
import pandas as pd
from django.db.models import F, Avg, Sum




class ResemplePvTechnicalDataTo15Min(models.Manager):
    # This manager is used to resample the technical data to 15 minutes. Currently the data is stored in 1 minutes interval
    def get_queryset(self):
        return super().get_queryset()
        
    def resample_to_15min(self):

        # Retrieve the data from the database
        data = self.get_queryset().values('timestamp', 'parameter_id', 'signal_value', 'installation_name')

        # Determine the aggregation function based on parameter_id
        aggregation_function = Sum('signal_value') if data[0]['parameter_id'] == 720 else Avg('signal_value')

        # Resample the data to 15 minutes intervals using Django ORM
        resampled_data = (
            data.annotate(
                rounded_timestamp=models.functions.TruncMinute('timestamp', precision=15)
            )
            .values('rounded_timestamp', 'parameter_id', 'installation_name')
            .annotate(signal_value=aggregation_function)
            .order_by('rounded_timestamp')
        )

        return resampled_data

        
       
class ConfidanceManager(models.Manager):
        
        def get_queryset(self):
            return super().get_queryset()
        

        def calculate_confidance(self, initial_date):
            start_date = initial_date - timedelta(days=8)
            query = PvMeasurementData.objects.filter(timestamp__range=[start_date, initial_date])
            
            if not query.exists():
                print("No data available for the given range.")
                return

            data = query.values('id', 'timestamp', 'production', 'farm', 'ppe')
            df = pd.DataFrame(data)

            if df.empty:
                print("There are no data!")
                return

            # Process data
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['production'] = pd.to_numeric(df['production'], errors='coerce')
            df['time'] = df['timestamp'].dt.strftime('%H:%M')
            
            # Group by PPE and time to calculate min and max
            grouped = df.groupby(['ppe', 'time'])['production']
            result = grouped.agg(production_min='min', production_max='max').reset_index()

            # Prepare for updates/creation
            start_period = initial_date
            end_period = start_period + timedelta(days=1)
            existing_data = PvMeasurementData.objects.filter(timestamp__range=(start_period, end_period))
            
            existing_map = {(obj.ppe, obj.timestamp.strftime('%H:%M')): obj for obj in existing_data}
            objs_to_update = []
            objs_to_create = []

            for _, row in result.iterrows():
                timestamp_str = f"{start_period} {row['time']}:00"
                timestamp = pd.to_datetime(timestamp_str)

                key = (row['ppe'], row['time'])
                if key in existing_map:
                    obj = existing_map[key]
                    obj.min_production = row['production_min']
                    obj.max_production = row['production_max']
                    objs_to_update.append(obj)
                else:
                    objs_to_create.append(
                        PvMeasurementData(
                            timestamp=timestamp,
                            ppe=row['ppe'],
                            min_production=row['production_min'],
                            max_production=row['production_max']
                        )
                    )

            # Perform bulk operations
            if objs_to_create:
                PvMeasurementData.objects.bulk_create(objs_to_create)
            if objs_to_update:
                PvMeasurementData.objects.bulk_update(objs_to_update, ['min_production', 'max_production'])    


class LastNUniqueDataPointsManager(models.Manager):    
    def get_queryset(self):        
        queryset = super().get_queryset()
        queryset = queryset.filter(parameter_id=719)
        last_record = queryset.order_by('-timestamp').first()
        if last_record:
            today = last_record.timestamp.date()
        else:
            today = datetime.now().date()

        unique_ppe = set()
        unique_data = []
        filtered_queryset = queryset.filter(timestamp__date=today).order_by('-timestamp')
        for item in filtered_queryset:
            if item.signal_uid not in unique_ppe:
                unique_ppe.add(item.signal_uid)                
                unique_data.append(item)
        
        return unique_data
    


class PvTechnicalData(models.Model):
    # This model is used to store the technical data of the PV installation fetched from the API
    parameter_id = models.IntegerField()
    installation_name = models.CharField(max_length=100)
    signal_uid = models.CharField(max_length=100)
    timestamp = models.DateTimeField()
    signal_value = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=10)
    unique_data = LastNUniqueDataPointsManager()
    objects = models.Manager()
    resample = ResemplePvTechnicalDataTo15Min()
    def __str__(self):
        return f"{self.installation_name} - {self.signal_uid}"
    


class PvMeasurementData(models.Model):
    # This model is used to store the actual measurement data    
    timestamp = models.DateTimeField(default=datetime.now)
    production = models.FloatField(null=True, blank=True)
    ppe = models.CharField(max_length=50, default='')  # Assuming PPE values are strings
    farm = models.CharField(max_length=100, default='')
    latitude = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    longitude = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    temperature_2m = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    uv_index = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    direct_radiation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_production = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    max_production = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    objects = models.Manager()
    confidance = ConfidanceManager()
    
    class Meta:
        unique_together = ('timestamp', 'ppe')
    

class ForecastDataDayAhead(models.Model):
    # This model is used to store the forecast data
    timestamp = models.DateTimeField()
    production_forecast = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    farm = models.CharField(max_length=100)
    ppe = models.CharField(max_length=50) 
    min_production = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    max_production = models.DecimalField(max_digits=10, decimal_places=3, default=0)

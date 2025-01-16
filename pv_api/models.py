from django.db import models

class PvTechnicalData(models.Model):
    # This model is used to store the technical data of the PV installation fetched from the API
    parameter_id = models.IntegerField()
    installation_name = models.CharField(max_length=100)
    signal_uid = models.CharField(max_length=100)
    signal_time = models.DateTimeField()
    signal_value = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.installation_name} - {self.signal_uid}"
    


class PvMeasurementData(models.Model):
    # This model is used to store the actual measurement data    
    timestamp = models.DateTimeField()
    production = models.DecimalField(max_digits=10, decimal_places=3)
    ppe = models.CharField(max_length=50)  # Assuming PPE values are strings
    farm = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=4)
    longitude = models.DecimalField(max_digits=10, decimal_places=4)
    temperature_2m = models.DecimalField(max_digits=10, decimal_places=2)
    uv_index = models.DecimalField(max_digits=10, decimal_places=2)
    direct_radiation = models.DecimalField(max_digits=10, decimal_places=2)
    min_production = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    max_production = models.DecimalField(max_digits=10, decimal_places=3, default=0)
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

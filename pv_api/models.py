from django.db import models

class PvData(models.Model):
    parameter_id = models.IntegerField()
    installation_name = models.CharField(max_length=100)
    signal_uid = models.CharField(max_length=100)
    signal_time = models.DateTimeField()
    signal_value = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.installation_name} - {self.signal_uid}"
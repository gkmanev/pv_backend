import random
from decimal import Decimal, InvalidOperation
from django.utils.dateparse import parse_datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from pv_api.models import PvMeasurementData
from datetime import datetime, timedelta, timezone


class Command(BaseCommand):
    help = 'Import data from combined_weather_and_df_dam.csv into PvMeasurementData'

    def handle(self, *args, **kwargs):
        # Get the last item from farm Arcus from PvMeasurementData and get the date
        last_item = PvMeasurementData.objects.filter(farm='Arcus').latest('timestamp')
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        # Create 96 objects on every 15 min for today start from 00:00 today
        for i in range(96):
            # Create a new timestamp for every 15 min
            timestamp = today + timedelta(minutes=15*i)
            # Determine production value based on the hour of the timestamp
            if 6 <= timestamp.hour < 16:
                production = round(random.uniform(0.02, 0.5), 2)
            else:
                production = 0
            # Check if the timestamp is greater than the last timestamp in the database
            if timestamp > last_item.timestamp:
                PvMeasurementData.objects.create(
                    timestamp=timestamp,
                    production=production,
                    ppe=0,
                    farm='Arcus',
                    latitude=0,
                    longitude=0,
                    temperature_2m=0,
                    uv_index=0,
                    direct_radiation=0,
                )
                # Print created timestamps
                self.stdout.write(self.style.SUCCESS(f"Created timestamp: {timestamp} with production: {production}"))
        self.stdout.write(self.style.SUCCESS("Inserted 96 records..."))
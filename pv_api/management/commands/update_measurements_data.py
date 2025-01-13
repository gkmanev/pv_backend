import os
import pandas as pd
from decimal import Decimal, InvalidOperation
from django.utils.dateparse import parse_datetime
from django.core.management.base import BaseCommand
from pv_api.models import PvMeasurementData

class Command(BaseCommand):
    help = 'Import data from combined_weather_and_df_dam.csv into PvMeasurementData'

    def handle(self, *args, **kwargs):
        file_path = 'combined_weather_and_df_dam.csv'

        # Check if the file exists
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File {file_path} does not exist."))
            return

        # Read the CSV file
        data = pd.read_csv(file_path)

        data = data.reset_index()


        # Iterate over the rows of the DataFrame
        for row in data.itertuples(index=False):
            try:
                self.stdout.write(self.style.SUCCESS(f"Processing row {row.index}"))
                if not PvMeasurementData.objects.filter(timestamp=parse_datetime(row.Timestamp), ppe=row.PPE).exists():
                    PvMeasurementData.objects.create(
                        timestamp=parse_datetime(row.Timestamp),
                        production=self.to_decimal(row.Production),
                        ppe=row.PPE,
                        farm=row.farm,
                        latitude=self.to_decimal(row.latitude),
                        longitude=self.to_decimal(row.longitude),
                        temperature_2m=self.to_decimal(row.temperature_2m),
                        uv_index=self.to_decimal(row.uv_index),
                        direct_radiation=self.to_decimal(row.direct_radiation),
                    )
                if row.index % 100 == 0:
                    self.stdout.write(self.style.SUCCESS(f"Processed {row.index} rows..."))
            except InvalidOperation as e:
                self.stdout.write(self.style.ERROR(f"Invalid data in row {row.index}: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing row {row.index}: {e}"))

        self.stdout.write(self.style.SUCCESS('Successfully imported data from CSV'))

    def to_decimal(self, value):
        try:
            self.stdout.write(self.style.SUCCESS(f"Converting value to Decimal: {value}"))
            return Decimal(str(value))
        except InvalidOperation:
            self.stdout.write(self.style.ERROR(f"InvalidOperation for value: {value}"))
            raise

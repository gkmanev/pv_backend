import os
import pandas as pd
from decimal import Decimal, InvalidOperation
import roman
from django.utils.dateparse import parse_datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from pv_api.models import PvMeasurementData


class Command(BaseCommand):
    help = 'Import data from combined_weather_and_df_dam.csv into PvMeasurementData'

    def handle(self, *args, **kwargs):
        file_path = 'combined_weather_and_df_dam.csv'
        chunksize = 10000  # Process CSV in chunks of 10,000 rows

        # Check if the file exists
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File {file_path} does not exist."))
            return

        # Preload existing records into memory
        self.stdout.write(self.style.SUCCESS("Loading existing records..."))
        existing_records = set(
            PvMeasurementData.objects.values_list('timestamp', 'ppe')
        )
        self.stdout.write(self.style.SUCCESS("Existing records loaded."))

        # Read and process CSV in chunks
        self.stdout.write(self.style.SUCCESS("Starting data import..."))
        for chunk in pd.read_csv(file_path, chunksize=chunksize):
            chunk = chunk.reset_index()
            records = []

            for row in chunk.itertuples(index=False):
                try:
                    # Check if record already exists
                    if (parse_datetime(row.Timestamp), row.PPE) not in existing_records:
                        # Replace any number in row.farm with its Roman numeral equivalent
                        farm = ''.join([str(roman.toRoman(int(char))) if char.isdigit() else char for char in row.farm])
                        production=self.to_decimal(row.Production)
                        records.append(
                            PvMeasurementData(
                                timestamp=parse_datetime(row.Timestamp),
                                production=production*1000,
                                ppe=row.PPE,
                                farm=farm,
                                latitude=self.to_decimal(row.latitude),
                                longitude=self.to_decimal(row.longitude),
                                temperature_2m=self.to_decimal(row.temperature_2m),
                                uv_index=self.to_decimal(row.uv_index),
                                direct_radiation=self.to_decimal(row.direct_radiation),
                            )
                        )

                    # Insert in batches of 1000
                    if len(records) >= 1000:
                        self.bulk_insert(records)
                        records = []  # Reset the batch
                        self.stdout.write(self.style.SUCCESS("Inserted 1000 records..."))

                except InvalidOperation as e:
                    self.stdout.write(self.style.ERROR(f"Invalid data in row: {e}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing row: {e}"))

            # Insert remaining records
            if records:
                self.bulk_insert(records)

        self.stdout.write(self.style.SUCCESS('Successfully imported data from CSV'))

    def to_decimal(self, value):
        """Convert a value to Decimal or return None if invalid."""
        try:
            return Decimal(str(value))
        except InvalidOperation:
            self.stdout.write(self.style.ERROR(f"InvalidOperation for value: {value}"))
            return None

    @transaction.atomic
    def bulk_insert(self, records):
        """Insert records into the database using bulk_create."""
        PvMeasurementData.objects.bulk_create(records)

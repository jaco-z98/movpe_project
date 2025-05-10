from django.db import models

# Create your models here.

class RawMeasurement(models.Model):
    data_file_id = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField()
    heater_temp = models.FloatField(null=True, blank=True)
    epi_reflect1_1 = models.FloatField(null=True, blank=True)
    epi_reflect1_2 = models.FloatField(null=True, blank=True)
    epi_reflect1_3 = models.FloatField(null=True, blank=True)
    tmga_1_run = models.FloatField(null=True, blank=True)
    tmal_1_run = models.FloatField(null=True, blank=True)
    nh3_1_run = models.FloatField(null=True, blank=True)
    sih4_1_run = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        app_label = 'raw_data'

    def __str__(self):
        return f"Measurement at {self.timestamp}"

    @property
    def data_file(self):
        from data_app.models import DataFile
        return DataFile.objects.get(id=self.data_file_id)

class RawMeasurement2(models.Model):
    data_file_id = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Dynamic columns for intensity values (0-358 degrees)
    for angle in range(0, 360, 2):
        locals()[f'intensity_{angle}'] = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']
        app_label = 'raw_data'

    def __str__(self):
        return f"Measurement2 at {self.timestamp}"

    @property
    def data_file(self):
        from data_app.models import DataFile
        return DataFile.objects.get(id=self.data_file_id)

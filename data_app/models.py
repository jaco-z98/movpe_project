from django.db import models


class DataFile(models.Model):
    file = models.FileField(upload_to='csv_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Plik {self.id} – {self.file.name}"


class MeasurementResult(models.Model):
    data_file = models.ForeignKey(DataFile, on_delete=models.CASCADE, related_name='results')

    # Podstawowe parametry
    average_intensity = models.FloatField()
    max_intensity = models.FloatField()
    min_intensity = models.FloatField()

    # Rozszerzone parametry
    variance_intensity = models.FloatField(null=True, blank=True)       # wariancja intensywności
    angle_range = models.FloatField(null=True, blank=True)              # zakres kątów
    duration_seconds = models.FloatField(null=True, blank=True)         # czas trwania w sekundach
    measurement_count = models.IntegerField(null=True, blank=True)      # liczba pomiarów

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wyniki pliku {self.data_file.id} – avg: {self.average_intensity:.3f}, max: {self.max_intensity:.2f}"


class ProcessMeasurement(models.Model):
    data_file = models.ForeignKey(DataFile, on_delete=models.CASCADE, related_name='process_measurements')
    parameter_name = models.CharField(max_length=100)
    average_value = models.FloatField()
    min_value = models.FloatField()
    max_value = models.FloatField()
    variance_value = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.parameter_name} – avg: {self.average_value:.2f} (plik {self.data_file.id})"


class RawMeasurement(models.Model):
    data_file = models.ForeignKey(DataFile, on_delete=models.CASCADE, related_name='raw_measurements')
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

    def __str__(self):
        return f"Measurement at {self.timestamp}"

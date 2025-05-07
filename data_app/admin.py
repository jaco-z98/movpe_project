from django.contrib import admin
from .models import DataFile, MeasurementResult


@admin.register(DataFile)
class DataFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('file',)


@admin.register(MeasurementResult)
class MeasurementResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_file', 'average_intensity', 'max_intensity', 'min_intensity', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('data_file__file',)

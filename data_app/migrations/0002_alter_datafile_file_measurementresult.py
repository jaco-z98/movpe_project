# Generated by Django 5.1.7 on 2025-04-15 11:01

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafile',
            name='file',
            field=models.FileField(upload_to='csv_files/'),
        ),
        migrations.CreateModel(
            name='MeasurementResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('average_intensity', models.FloatField()),
                ('max_intensity', models.FloatField()),
                ('min_intensity', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('data_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='data_app.datafile')),
            ],
        ),
    ]

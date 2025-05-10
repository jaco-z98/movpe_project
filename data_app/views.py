import pandas as pd
import numpy as np
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import DataFileForm
from .models import DataFile, MeasurementResult, ProcessMeasurement
from raw_data.models import RawMeasurement, RawMeasurement2
import plotly.graph_objs as go
from plotly.offline import plot
from scipy.interpolate import UnivariateSpline
import warnings
import os
from django.utils import timezone

warnings.filterwarnings("ignore", category=UserWarning)

def detect_file_type(df):
    numeric_columns = df.columns[1:]
    try:
        float_labels = pd.to_numeric(numeric_columns, errors='coerce')
        if float_labels.notnull().sum() > 10:
            return 'interferogram'
    except:
        pass
    return 'process'

def get_time_scaled(seconds, scale):
    if scale == 'minutes':
        return seconds / 60.0
    elif scale == 'hours':
        return seconds / 3600.0
    return seconds

def get_tick_params(scale):
    if scale == 'seconds':
        return {"dtick": 240, "tickformat": ",d"}
    elif scale == 'minutes':
        return {"dtick": 2, "tickformat": ".1f"}
    elif scale == 'hours':
        return {"dtick": 0.5, "tickformat": ".1f"}
    return {}

def calculate_parameters(datafile):
    try:
        df = pd.read_csv(datafile.file.path, sep=';')
        df.iloc[:, 0] = pd.to_datetime("2000-01-01 " + df.iloc[:, 0], errors='coerce')
        df = df.dropna(subset=[df.columns[0]])

        file_type = detect_file_type(df)

        if file_type == 'interferogram':
            angle_labels = pd.to_numeric(df.columns[1:], errors='coerce')
            data_matrix = df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce').dropna(axis=1, how='all').values
            valid_labels = angle_labels[~np.isnan(angle_labels)]

            MeasurementResult.objects.create(
                data_file=datafile,
                average_intensity=np.nanmean(data_matrix),
                max_intensity=np.nanmax(data_matrix),
                min_intensity=np.nanmin(data_matrix),
                variance_intensity=np.nanvar(data_matrix),
                duration_seconds=(df.iloc[-1, 0] - df.iloc[0, 0]).total_seconds(),
                measurement_count=data_matrix.shape[0],
                angle_range=valid_labels.max() - valid_labels.min()
            )
        else:
            numeric_data = df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce').dropna(axis=1, how='all')
            for col in numeric_data.columns:
                col_data = numeric_data[col].dropna()
                if col_data.empty:
                    continue
                ProcessMeasurement.objects.create(
                    data_file=datafile,
                    parameter_name=col,
                    average_value=col_data.mean(),
                    min_value=col_data.min(),
                    max_value=col_data.max(),
                    variance_value=col_data.var()
                )
    except Exception as e:
        print(f"Błąd podczas obliczania parametrów: {e}")

def load_raw_data(file_path, data_file_id):
    """Load raw data from CSV file into the database"""
    try:
        # Read the first few lines to determine the format
        with open(file_path, 'r') as f:
            first_line = f.readline().strip()
            second_line = f.readline().strip()
        
        print("First line:", first_line)
        print("Second line:", second_line)
        
        # Check if this is the first format (with Heater.temp.Current Value)
        is_first_format = 'Heater.temp.Current Value' in first_line
        
        df = pd.read_csv(file_path, sep=';')

        measurements = []

        if is_first_format:
            df.iloc[:, 0] = pd.to_datetime("2000-01-01 " + df.iloc[:, 0], errors='coerce')
            df = df.dropna(subset=[df.columns[0]])
            column_mapping = {
                'Time (abs)': 'timestamp',
                'Heater.temp.Current Value': 'heater_temp',
                'EpiReflect1_1.Current Value': 'epi_reflect1_1',
                'EpiReflect1_2.Current Value': 'epi_reflect1_2',
                'EpiReflect1_3.Current Value': 'epi_reflect1_3',
                'TMGa_1.run.Current Value': 'tmga_1_run',
                'TMAl_1.run.Current Value': 'tmal_1_run',
                'NH3_1.run.Current Value': 'nh3_1_run',
                'SiH4_1.run.Current Value': 'sih4_1_run'
            }

            # Rename columns to match model fields
            df = df.rename(columns=column_mapping)

            # Convert all numeric columns to float
            for col in df.columns:
                if col != 'timestamp':
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Create RawMeasurement objects in bulk
            measurements = []
            for _, row in df.iterrows():
                measurement = RawMeasurement(
                    data_file_id=data_file_id,
                    timestamp=row['timestamp'],
                    heater_temp=row.get('heater_temp'),
                    epi_reflect1_1=row.get('epi_reflect1_1'),
                    epi_reflect1_2=row.get('epi_reflect1_2'),
                    epi_reflect1_3=row.get('epi_reflect1_3'),
                    tmga_1_run=row.get('tmga_1_run'),
                    tmal_1_run=row.get('tmal_1_run'),
                    nh3_1_run=row.get('nh3_1_run'),
                    sih4_1_run=row.get('sih4_1_run')
                )
                measurements.append(measurement)
            RawMeasurement.objects.using('raw_measurements').bulk_create(measurements)
        else:
            # Second format - process angle-based data
            print("\nSecond format columns:")
            print(df.columns.tolist())
            
            # Convert Time / Angle column to datetime
            df['Time / Angle'] = pd.to_datetime(df['Time / Angle'])
            
            print("Time column:", df['Time / Angle'].head())
            
            for _, row in df.iterrows():
                measurement = RawMeasurement2.objects.create(
                    data_file_id=data_file_id,
                    timestamp=row['Time / Angle']
                )
                
                # Set intensity values for each angle
                for angle in range(0, 360, 2):
                    column_name = str(angle)
                    if column_name in row:
                        setattr(measurement, f'intensity_{angle}', row[column_name])
                
                measurements.append(measurement)
            
            RawMeasurement.objects.using('raw_measurements_2').bulk_create(measurements)

        return True
    except Exception as e:
        print(f"Error loading raw data: {str(e)}")
        return False

def index(request):
    print(">>>>>>>>index")
    chart_2d = None
    chart_3d = None
    x_slider_max = 0
    y_slider_values = []
    results = MeasurementResult.objects.all().order_by('-created_at')
    process_parameters = ProcessMeasurement.objects.values_list('parameter_name', flat=True).distinct()
    scale = request.GET.get('scale', 'seconds')

    if request.method == 'POST':
        form = DataFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = form.save()
            # Load raw data first
            load_raw_data(file_instance.file.path, file_instance.id)
            # Then calculate parameters
            calculate_parameters(file_instance)
            return redirect('index')
    else:
        form = DataFileForm()

    last_file = DataFile.objects.last()
    if last_file:
        print(">>>>>>>>index read_csv")
        df = pd.read_csv(last_file.file.path, sep=';')
        df[df.columns[0]] = pd.to_datetime("2000-01-01 " + df[df.columns[0]], errors='coerce')
        df = df.dropna(subset=[df.columns[0]])

        try:
            angle_labels = pd.to_numeric(df.columns[1:], errors='coerce')
            valid_data = df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce').dropna(axis=1, how='all')
            time_seconds = (df[df.columns[0]] - df[df.columns[0]].iloc[0]).dt.total_seconds()
            time_scaled = get_time_scaled(time_seconds, scale)

            x_slider_max = len(time_scaled) - 1
            y_slider_values = angle_labels.tolist()

            tick_params = get_tick_params(scale)

            heatmap = go.Heatmap(
                z=valid_data.values.T,
                x=time_scaled,
                y=angle_labels,
                colorscale='Viridis',
                colorbar=dict(title='Intensywność')
            )
            layout_2d = go.Layout(
                xaxis=dict(title=f'Czas ({scale})', **tick_params),
                yaxis=dict(title='Kąt (°)')
            )
            chart_2d = plot(go.Figure(data=[heatmap], layout=layout_2d), output_type='div')

            surface = go.Surface(z=valid_data.values.T, x=time_scaled, y=angle_labels)
            layout_3d = go.Layout(title='Poglądowy wykres 3D', scene=dict(
                xaxis=dict(title=f'Czas ({scale})', **tick_params),
                yaxis=dict(title='Kąt (°)'),
                zaxis=dict(title='Intensywność')
            ))
            chart_3d = plot(go.Figure(data=[surface], layout=layout_3d), output_type='div')
        except Exception as e:
            print(f"Błąd przy wizualizacji: {e}")

    return render(request, 'index.html', {
        'form': form,
        'chart_2d': chart_2d,
        'chart_3d': chart_3d,
        'x_slider_max': x_slider_max,
        'y_slider_values': y_slider_values,
        'results': results,
        'process_parameters': process_parameters,
    })

def get_approximation_x(request):
    try:
        x_raw = str(request.GET.get('x', '0')).replace(',', '.')
        x_index = int(float(x_raw))
        if np.isnan(x_index):
            raise ValueError("Wartość x jest NaN")
    except Exception as e:
        return JsonResponse({'error': f'Nieprawidłowy indeks: {e}'})

    last_file = DataFile.objects.last()
    df = pd.read_csv(last_file.file.path, sep=';')
    df.iloc[:, 0] = pd.to_datetime("2000-01-01 " + df.iloc[:, 0].astype(str), errors='coerce')
    df = df.dropna(subset=[df.columns[0]])

    angle_labels = pd.to_numeric(df.columns[1:], errors='coerce')
    data_matrix = df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce').dropna(axis=1, how='all').values

    if x_index >= len(data_matrix) or x_index < 0:
        return JsonResponse({'error': 'Indeks poza zakresem danych'})

    intensity = data_matrix[x_index, :]
    valid = ~np.isnan(angle_labels) & ~np.isnan(intensity)

    if np.count_nonzero(valid) < 3:
        return JsonResponse({'error': 'Za mało danych do interpolacji'})

    try:
        spline = UnivariateSpline(angle_labels[valid], intensity[valid], s=0.5)
    except Exception as e:
        return JsonResponse({'error': f'Błąd interpolacji: {e}'})

    trace = {
        'x': angle_labels[valid].tolist(),
        'y': spline(angle_labels[valid]).tolist(),
        'type': 'scatter',
        'line': {'color': 'blue'}
    }
    raw_trace = {
        'x': angle_labels[valid].tolist(),
        'y': intensity[valid].tolist(),
        'type': 'scatter',
        'name': 'Oryginalne dane',
        'line': {'dash': 'dot', 'color': 'gray'}
    }

    layout = {
        'title': {'text': 'Intensywność względem kąta'},
        'xaxis': {'title': 'Kąt (°)'},
        'yaxis': {'title': 'Intensywność'}
    }

    return JsonResponse({'traces': [raw_trace, trace], 'layout': layout})

def get_approximation_y(request):
    try:
        y_val = float(str(request.GET.get('y', '0')).replace(',', '.'))
    except Exception as e:
        return JsonResponse({'error': f'Nieprawidłowa wartość kąta: {e}'})

    scale = request.GET.get('scale', 'seconds')

    last_file = DataFile.objects.last()
    df = pd.read_csv(last_file.file.path, sep=';')
    df.iloc[:, 0] = pd.to_datetime("2000-01-01 " + df.iloc[:, 0].astype(str), errors='coerce')
    df = df.dropna(subset=[df.columns[0]])

    timestamps = df.iloc[:, 0]
    timestamps = pd.to_datetime(timestamps, errors='coerce')
    timestamps = timestamps.dropna()
    time_seconds = (timestamps - timestamps.iloc[0]).dt.total_seconds()
    time_scaled = get_time_scaled(time_seconds, scale)

    angle_labels = pd.to_numeric(df.columns[1:], errors='coerce')
    data_matrix = df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce').dropna(axis=1, how='all').values

    y_index = np.abs(angle_labels - y_val).argmin()
    intensity = data_matrix[:, y_index]
    x_range = np.arange(len(intensity))
    valid = ~np.isnan(time_scaled) & ~np.isnan(intensity)

    try:
        spline = UnivariateSpline(x_range[valid], intensity[valid], s=0.5)
    except Exception as e:
        print(f"Błąd interpolacji Y: {e}")
        return JsonResponse({'error': 'Błąd interpolacji'})

    tick_params = get_tick_params(scale)

    trace = {
        'x': time_scaled.tolist(),
        'y': spline(x_range).tolist(),
        'type': 'scatter',
        'line': {'color': 'green'}
    }
    raw_trace = {
        'x': time_scaled.tolist(),
        'y': intensity.tolist(),
        'type': 'scatter',
        'name': 'Oryginalne dane',
        'line': {'dash': 'dot', 'color': 'gray'}
    }

    layout = {
        'title': {'text': 'Intensywność względem czasu'},
        'xaxis': {'title': f'Czas ({scale})', **tick_params},
        'yaxis': {'title': 'Intensywność'}
    }

    return JsonResponse({'traces': [raw_trace, trace], 'layout': layout})

def get_process_plot(request):
    param = request.GET.get("parameter")
    scale = request.GET.get("scale", "seconds")
    
    measurement = ProcessMeasurement.objects.filter(parameter_name=param).order_by('-created_at').first()
    if not measurement:
        return JsonResponse({'error': 'Nie znaleziono danych dla podanego parametru'})

    data_file = measurement.data_file
    df = pd.read_csv(data_file.file.path, sep=';')
    df.iloc[:, 0] = pd.to_datetime("2000-01-01 " + df.iloc[:, 0].astype(str), errors='coerce')
    df = df.dropna(subset=[df.columns[0]])

    timestamps = df.iloc[:, 0]
    time_seconds = (timestamps - timestamps.iloc[0]).dt.total_seconds()
    time_scaled = get_time_scaled(time_seconds, scale)
    tick_params = get_tick_params(scale)

    y = pd.to_numeric(df[param], errors='coerce')

    trace = {
        'x': time_scaled.tolist(),
        'y': y.tolist(),
        'type': 'scatter',
        'mode': 'lines+markers',
        'line': {'color': 'purple'},
        'name': param
    }

    layout = {
        'title': f'{param} względem czasu',
        'xaxis': {'title': f'Czas ({scale})', **tick_params},
        'yaxis': {'title': param}
    }

    return JsonResponse({'traces': [trace], 'layout': layout})

def preview_data(request):
    try:
        last_file = DataFile.objects.last()
        if not last_file:
            return render(request, 'preview.html', {'error': 'Brak plików w bazie.'})

        df = pd.read_csv(last_file.file.path, sep=';')
        df_html = df.head(30).to_html(classes='table table-bordered table-hover table-sm', index=False, table_id='csv-data')
        return render(request, 'preview.html', {
            'table': df_html,
            'columns': df.columns.tolist(),
            'data_json': df.to_json(orient='records')
        })
    except Exception as e:
        return render(request, 'preview.html', {'error': f'Błąd podczas wczytywania danych: {e}'})
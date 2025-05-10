class RawMeasurementRouter:
    """
    Router to handle RawMeasurement model operations
    """
    def db_for_read(self, model, **hints):
        if model._meta.model_name == 'rawmeasurement':
            return 'raw_measurements'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name == 'rawmeasurement':
            return 'raw_measurements'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations between RawMeasurement and DataFile
        if obj1._meta.model_name == 'rawmeasurement' or obj2._meta.model_name == 'rawmeasurement':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name == 'rawmeasurement':
            return db == 'raw_measurements'
        return None

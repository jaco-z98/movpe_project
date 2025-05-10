class RawMeasurementRouter:
    """
    Router to handle raw_data app operations
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'raw_data':
            return 'raw_measurements'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'raw_data':
            return 'raw_measurements'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations between RawMeasurement and DataFile
        if obj1._meta.app_label == 'raw_data' or obj2._meta.app_label == 'raw_data':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Only allow raw_data app to migrate to raw_measurements database
        if db == 'raw_measurements':
            return app_label == 'raw_data'
        # All other apps should only migrate to default database
        return db == 'default'

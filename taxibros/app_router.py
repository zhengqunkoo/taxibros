class AppRouter:
    """Determine how to route database calls for an app's models."""

    def db_for_read(self, model, **hints):
        """Send all read operations on Mouse app models to `mouse_db`."""
        if model._meta.app_label == "mouse":
            return "mouse_db"
        return None

    def db_for_write(self, model, **hints):
        """Send all write operations on Mouse app models to `mouse_db`."""
        if model._meta.app_label == "mouse":
            return "mouse_db"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Determine if relationship is allowed between two objects."""
        if obj1._meta.app_label == "mouse" and obj2._meta.app_label == "mouse":
            return True
        elif "mouse" not in [obj1._meta.app_label, obj2._meta.app_label]:
            return None
        return False

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that the Mouse app's models get created on the right database."""
        if app_label == "mouse":
            return db == "mouse_db"
        elif db == "mouse_db":
            return False
        return None

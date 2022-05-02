import os
import sys

from django.apps import AppConfig


class ManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'manager'

    def ready(self):
        # Using `python manage.py runserver`, Django start two processes,
        # one for the actual development server
        # and other to reload your application when the code changes.
        # Check if this is the actual development server to start background thread
        # Only run background thread on runserver
        if os.environ.get('RUN_MAIN', None) != 'true' and 'runserver' in sys.argv:
            # Start UHF modules manager thread on startup
            from .manager import modules_manager
            modules_manager.start()

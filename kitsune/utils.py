from django.conf import settings
from django.core.management import setup_environ
from django.utils.importlib import import_module

import os

def get_manage_py():
    module = import_module(settings.SETTINGS_MODULE)
    return os.path.join(setup_environ(module, settings.SETTINGS_MODULE), 'manage.py')
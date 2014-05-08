# -*- coding: utf-8 -
'''
Created on Mar 3, 2012

@author: Raul Garreta (raul@tryolabs.com)

Based on django-chronograph.

'''

__author__ = "Raul Garreta (raul@tryolabs.com)"


import os

import django
from django.conf import settings
from django.utils.importlib import import_module


def get_manage_py():
    module = import_module(settings.SETTINGS_MODULE)
    if django.get_version().startswith('1.3'):
        # This is dirty, but worked in django <= 1.3 ...
        from django.core.management import setup_environ
        return os.path.join(
            setup_environ(module, settings.SETTINGS_MODULE), 'manage.py'
        )
    else:
        # Dirty again, but this should work in django > 1.3
        # We should DEFINITELY do this in an elegant way ...
        settings_path = os.path.dirname(module.__file__)
        return os.path.join(settings_path, '..', 'manage.py')

# -*- coding: utf-8 -
'''
Created on Mar 3, 2012

@author: Raul Garreta (raul@tryolabs.com)

Defines the base Kitsune job renderer.
All custom Kitsune job renderers must extend KitsuneJobRenderer.
'''

__author__      = "Raul Garreta (raul@tryolabs.com)"


from django.template.loader import render_to_string

from kitsune.base import STATUS_OK, STATUS_WARNING, STATUS_CRITICAL, STATUS_UNKNOWN



class KitsuneJobRenderer():
    
    def get_html_status(self, log):
        return render_to_string('kitsune/status_code.html', dictionary={'status_code':int(log.stderr)})
        
    def get_html_message(self, log):
        result = log.stdout
        if len(result) > 40:
            result = result[:40] + '...'
        return result
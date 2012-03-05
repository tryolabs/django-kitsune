'''
Created on Mar 3, 2012

@author: raul
'''

from django.template.loader import render_to_string


# Exit status codes recognized by Nagios
STATUS_OK = 0
STATUS_WARNING = 1
STATUS_CRITICAL = 2
STATUS_UNKNOWN = 3


class KitsuneJobRenderer():
    
    def get_html_status(self, log):
        if log.stderr == unicode(STATUS_OK):
            return render_to_string('kitsune/success_status.html')
        elif log.stderr == unicode(STATUS_WARNING):
            return render_to_string('kitsune/alert_status.html')
        else:
            return render_to_string('kitsune/error_status.html')
        
    def get_html_message(self, log):
        result = log.stdout
        if len(result) > 40:
            result = result[:40] + '...'
        return result
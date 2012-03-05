'''
Created on Mar 3, 2012

@author: raul
'''

# Exit status codes recognized by Nagios
STATUS_OK = 0
STATUS_WARNING = 1
STATUS_CRITICAL = 2
STATUS_UNKNOWN = 3


class KitsuneJobRenderer():
    
    def get_html_status(self, log):
        if log.stderr == unicode(STATUS_OK):
            return '<img src="/static/admin/img/admin/icon_success.gif" alt="False">'
        elif log.stderr == unicode(STATUS_WARNING):
            return '<img src="/static/admin/img/admin/icon_alert.gif" alt="False">'
        else:
            return '<img src="/static/admin/img/admin/icon_error.gif" alt="False">'
        
    def get_html_message(self, log):
        result = log.stdout
        if len(result) > 40:
            result = result[:40] + '...'
        return result
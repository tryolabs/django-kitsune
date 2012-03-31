# -*- coding: utf-8 -
'''
Created on Mar 3, 2012

@author: Raul Garreta (raul@tryolabs.com)

Dummy check to test functionality.

'''

__author__      = "Raul Garreta (raul@tryolabs.com)"


from kitsune.renderers import STATUS_OK, STATUS_WARNING, STATUS_CRITICAL, STATUS_UNKNOWN
from kitsune.base import BaseKitsuneCheck


class Command(BaseKitsuneCheck):
    help = 'A simple test check.'
    
    
    def check(self, *args, **options):
        self.status_code = STATUS_OK
        
        if self.status_code == STATUS_OK:
            self.status_message = 'OK message'
        elif self.status_code == STATUS_WARNING:
            self.status_message = 'WARNING message'
        elif self.status_code == STATUS_CRITICAL:
            self.status_message = 'CRITICAL message'
        else:
            self.status_message = 'UNKNOWN message'
            

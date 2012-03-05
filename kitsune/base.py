# -*- coding: utf-8 -
'''
Created on Mar 5, 2012

@author: Raul Garreta (raul@tryolabs.com)

Defines base kitsune check.
All custom kitsune checks must define a Command class that extends BaseKitsuneCheck.

'''

__author__      = "Raul Garreta (raul@tryolabs.com)"

import sys
import traceback

from django.core.management.base import BaseCommand


# Exit status codes (also recognized by Nagios)
STATUS_OK = 0
STATUS_WARNING = 1
STATUS_CRITICAL = 2
STATUS_UNKNOWN = 3


class BaseKitsuneCheck(BaseCommand):
    
    def check(self):
        self.status_code = STATUS_OK
            
    def handle(self, *args, **options):
        try:
            self.check(*args, **options)
            #standard output to print status message
            print self.status_message,
            #standard error to print status code
            #note comma at the end to avoid printing a \n
            print >> sys.stderr, self.status_code,
        except Exception as e:
            trace = 'Trace: ' + traceback.format_exc()
            print str(e), trace, 'args:', args, 'options:', options
            print >> sys.stderr, STATUS_UNKNOWN,
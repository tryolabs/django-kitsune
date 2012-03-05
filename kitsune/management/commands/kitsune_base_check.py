import sys

from django.core.management.base import BaseCommand

from kitsune.renderers import STATUS_OK, STATUS_WARNING, STATUS_CRITICAL, STATUS_UNKNOWN


class BaseKitsuneCheck():
    pass


class Command(BaseCommand, BaseKitsuneCheck):
    help = 'A simple test check.'
    
    
    def check(self):
        self.status_code = STATUS_OK
        
        if self.status_code == STATUS_OK:
            self.status_message = 'OK message'
        elif self.status_code == STATUS_WARNING:
            self.status_message = 'WARNING message'
        elif self.status_code == STATUS_CRITICAL:
            self.status_message = 'CRITICAL message'
        else:
            self.status_message = 'UNKNOWN message'
            
            
    def handle(self, *args, **options):
        self.check()
        #standard output to print status message
        print self.status_message
        #standard error to print status code
        #note comma at the end to avoid printing a \n
        print >> sys.stderr, self.status_code,
        

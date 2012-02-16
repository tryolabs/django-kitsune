from django.core.management.base import BaseCommand
from kitsune.models import Job

import sys

from time import sleep

help_text = '''
Emulates a reoccurring cron call to run jobs at a specified interval.
This is meant primarily for development use.
'''

class Command(BaseCommand):
    help = help_text
    args = "time"
    
    def handle( self, *args, **options ):
        from django.core.management import call_command
        try:
            t_wait = int(args[0])
        except:
            t_wait = 60
        try:
            print "Starting cronserver.  Jobs will run every %d seconds." % t_wait
            print "Quit the server with CONTROL-C."
            
            # Run server untill killed
            while True:
                for job in Job.objects.all():
                    p = job.run(False)
                    if p is not None:
                        print "Running: %s" % job
                sleep(t_wait)
        except KeyboardInterrupt:
            print "Exiting..."
            sys.exit()
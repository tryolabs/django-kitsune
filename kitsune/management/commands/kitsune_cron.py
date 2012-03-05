# -*- coding: utf-8 -
'''
Created on Mar 3, 2012

@author: Raul Garreta (raul@tryolabs.com)

Management command called by cron.
Calls run for all jobs.

Based on django-chronograph.

'''

__author__      = "Raul Garreta (raul@tryolabs.com)"


from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Runs all jobs that are due.'
    
    def handle(self, *args, **options):
        from kitsune.models import Job
        procs = []
        for job in Job.objects.all():
            p = job.run(False)
            if p is not None:
                procs.append(p)
        for p in procs:
            p.wait()
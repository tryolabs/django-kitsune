from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'A simple test check.'
    
    def handle(self, *args, **options):
        print "All is OK!"
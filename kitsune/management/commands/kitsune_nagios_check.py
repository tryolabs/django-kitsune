# -*- coding: utf-8 -
'''
Created on Mar 5, 2012

@author: Raul Garreta (raul@tryolabs.com)

Kitsune check that wrapps any Nagios check.
All necessary parameters must be passed through args field at admin interface.
A special option: "check" must be passed with the name of the Nagios check to run.
eg:
check=check_disk -u=GB -w=5 -c=2 -p=/

'''

__author__      = "Raul Garreta (raul@tryolabs.com)"


from kitsune.base import BaseKitsuneCheck
from kitsune.nagios import NagiosPoller
from kitsune.monitor import ArgSet


class Command(BaseKitsuneCheck):
    help = 'A Nagios check.'
    
    
    def check(self, *args, **options):
        poller = NagiosPoller()
        nagios_args = ArgSet()
        check = options['check']
        del options['check']
        del options['verbosity']
        
        new_args = []
        for arg in args:
            if arg != 'verbosity':
                new_args.append(arg)
        args = new_args
                
        for arg in args:
            nagios_args.add_argument(arg)
        for option in options:
            nagios_args.add_argument_pair(str(option), str(options[option]))
        res = poller.run_plugin(check, nagios_args)
        
        self.status_code = res.returncode
        self.status_message = " NAGIOS_OUT:  " + res.output + "<br>NAGIOS_ERR:  " + res.error
            
        
        

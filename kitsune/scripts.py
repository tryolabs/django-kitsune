'''
Created on Mar 5, 2012

@author: raul
'''


from nagios import NagiosPoller
from monitor import ArgSet


def check_http():
    poller = NagiosPoller()
    args = ArgSet()
    args.add_argument_pair("-H", "liukang.tryolabs.com")
    args.add_argument_pair("-p", "80")
    res = poller.run_plugin('check_http', args)
    print "\n",res.command,"\nRET CODE:\t",res.returncode,"\nOUT:\t\t",res.output,"\nERR:\t\t",res.error
    
    
def check_ping():
    poller = NagiosPoller()
    args = ArgSet()
    args.add_argument_pair("-H", "google.com")
    args.add_argument_pair("-w", "200.0,20%")
    args.add_argument_pair("-c", "500.0,60%")
    res = poller.run_plugin('check_ping', args)
    print "\n",res.command,"\nRET CODE:\t",res.returncode,"\nOUT:\t\t",res.output,"\nERR:\t\t",res.error
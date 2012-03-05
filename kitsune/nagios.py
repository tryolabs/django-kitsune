#!/usr/bin/env python
# encoding: utf-8
"""
nagios.py

Class to invoke nagios plugins and return the results in a structured format.

Created by Joseph Heck on 2009-10-24.

"""
import os
import sys
import re
import subprocess
import datetime
from monitor import ArgSet
from monitor import MonitorResult
from monitor import MonitoringPoller


class NagiosPoller(MonitoringPoller):
    """a class that invokes a Nagios plugin and returns the result"""
    def __init__(self):
        """default initialization"""
        MonitoringPoller.__init__(self)
        self.plugin_dir = "/usr/local/nagios/libexec"  # default - aiming for RHEL5 instance of nagios-plugins
        if os.path.exists("/usr/lib/nagios/plugins"):  # ubuntu's apt-get install nagios-plugins
            self.plugin_dir = "/usr/lib/nagios/plugins"
        if os.path.exists("/opt/local/libexec/nagios"):  # MacOS X port install nagios-plugins
            self.plugin_dir = "/opt/local/libexec/nagios"
        self._internal_plugin_list = []
        self._load_plugin_list()
        self.uom_parsecode = re.compile('([\d\.]+)([a-zA-Z%]*)')
        self.poller_kind = "eyeswebapp.util.nagios.NagiosPoller"

    def _load_plugin_list(self):
        """ load in the plugins from the directory 'plugin_dir' set on the poller..."""
        self._internal_plugin_list = []
        raw_list = os.listdir(self.plugin_dir)
        for potential in raw_list:
            if potential.startswith("check_"):
                self._internal_plugin_list.append(potential)

    def plugin_list(self):
        """ returns the internal list of plugins available to Nagios"""
        return self._internal_plugin_list

    def plugin_help(self, plugin_name):
        """invoke --help on the named plugin, return the results"""
        argset = ArgSet()
        argset.add_argument('--help')
        return self.run_plugin(plugin_name, argset)

    def _invoke(self, plugin_name, list_of_args=None):
        """parse and invoke the plugin. method accepts the plugin name and then a list of arguments to be invoked.
        The return value is either None or a dictionary with the following keys:
        * command - the command invoked on the command line from the poller
        * output - the standard output from the command, strip()'d
        * error - the standard error from the command, strip()'d
        """
        if plugin_name is None:
            return None
        monresult = MonitorResult()
        cmd = os.path.join(self.plugin_dir, plugin_name)
        if not os.path.exists(cmd):
            monresult.error = "No plugin named %s found." % plugin_name
            monresult.timestamp = datetime.datetime.now()
            monresult.returncode = 3
            return monresult
        if not(list_of_args is None):
            for arg in list_of_args:
                cmd += " %s" % arg
        monresult.command = cmd.strip()
        if sys.platform == 'win32':
            close_fds = False
        else:
            close_fds = True
        #
        process = subprocess.Popen(cmd, shell=True, close_fds=close_fds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdoutput, stderror) = process.communicate()
        monresult.timestamp = datetime.datetime.now()
        monresult.returncode = process.returncode
        if (stdoutput):
            cleaned_out = stdoutput.strip()
            monresult.output = cleaned_out
            monresult.decoded = MonitorResult.parse_nagios_output(cleaned_out)
        if (stderror):
            cleaned_err = stderror.strip()
            monresult.error = cleaned_err
        return monresult

    def run_plugin(self, plugin_name, argset=None):
        """run_plugin is the primary means of invoking a Nagios plugin. It takes a plugin_name, such
        as 'check_ping' and an optional ArgSet object, which contains the arguments to run the plugin
        on the command line.

        Example results:
        >>> xyz = NagiosPoller()
        >>> ping_argset = ArgSet()
        >>> ping_argset.add_argument_pair("-H", "localhost")
        >>> ping_argset.add_argument_pair("-w", "1,99%")
        >>> ping_argset.add_argument_pair("-c", "1,99%")
        >>> monitor_result = xyz.run_plugin('check_ping', ping_argset)
        >>> print monitor_result.command
        /opt/local/libexec/nagios/check_ping -H localhost -w 1,99% -c 1,99%
        >>> print monitor_result.output
        PING OK - Packet loss = 0%, RTA = 0.14 ms|rta=0.137000ms;1.000000;1.000000;0.000000 pl=0%;99;99;0
        >>> print monitor_result.error

        >>> print monitor_result.returncode
        0
        >>> abc = NagiosPoller()
        >>> http_argset = ArgSet()
        >>> http_argset.add_argument_pair("-H", "www.google.com")
        >>> http_argset.add_argument_pair("-p", "80")
        >>> mon_result = abc.run_plugin('check_http', http_argset)
        >>> print monitor_result.command
        Traceback (most recent call last):
          File "<console>", line 1, in <module>
        NameError: name 'monitor_result' is not defined
        >>> print mon_result.command
        /opt/local/libexec/nagios/check_http -H www.google.com -p 80
        >>> print mon_result.output
        HTTP OK: HTTP/1.1 200 OK - 9047 bytes in 0.289 second response time |time=0.288865s;;;0.000000 size=9047B;;;0
        >>> print mon_result.error

        >>> print mon_result.returncode
        0
        """
        if argset is None:
            monitor_result = self._invoke(plugin_name)  # returns a MonitorResult object
        else:
            monitor_result = self._invoke(plugin_name, argset.list_of_arguments())  # returns a MonitorResult object
        return monitor_result

# if __name__ == '__main__':
#     import pprint
#     xyz = NagiosPoller()
#     ping_argset = ArgSet()
#     ping_argset.add_argument_pair("-H", "localhost")
#     ping_argset.add_argument_pair("-w", "1,99%")
#     ping_argset.add_argument_pair("-c", "1,99%")
#     ping_result = xyz.run_plugin('check_ping', ping_argset)
#     print ping_result.json()
#
#     abc = NagiosPoller()
#     http_argset = ArgSet()
#     http_argset.add_argument_pair("-H", "www.google.com")
#     http_argset.add_argument_pair("-p", "80")
#     http_result = abc.run_plugin('check_http', http_argset)
#     print http_result.json()

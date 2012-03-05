""" Utility interface classes for passing information off to pollers (ArgSet) or receiving results to be
published against existing Monitors."""

import simplejson
import dateutil.parser
import datetime
import re


class MonitoringPoller:
    """ Abstract base class for the pollers that Eyes runs. Each poller is expected to have
    the following functions:
      run_plugin(plugin_name, argset)
      plugin_help(plugin_name)
      plugin_list()
    """

    def run_plugin(self, plugin_name, argset=None):
        """ runs the plugin and returns the results in the form of a MonitorResult object"""
        raise NotImplementedError

    def plugin_help(self, plugin_name):
        """ runs the given plugin function to get interactive help results. Intended to
        return sufficient information to create an ArgSet object to run the poller properly."""
        raise NotImplementedError

    def plugin_list(self):
        """ returns a list of the plugins that this poller provides. And of the list of
        plugins should be able to be invoked with plugin_help(plugin_name) to get a response back
        that includes sufficient information to create an ArgSet and invoke the plugin
        to monitor a remote system."""
        return None

    def __init__(self):
        """default initialization"""
        self.poller_kind = "eyeswebapp.util.baseclass"


class MonitorResult:
    """
    A class representation of the dictionary structure that a monitor returns as it's
    combined result set. A MonitorResult can be serialized and deserialized into JSON
    and includes a structured segment to return multiple counts/values as a part of a monitor
    invocation, either active of passive. Initial structure of MonitorResult is based on the
    data that a Nagios plugin returns.

    The internal dictionary structure:
    ** command - string
    ** error - string or None
    ** returncode - integer
    ** timestamp - string of a datestamp (ISO format)
    ** output - string or None
    ** decoded - a dictionary
    ** decoded must have the following keys:
    *** human - a string
    *** 1 or more other keys, which are strings
    *** for each key other than human, the following keys must exist:
    **** UOM - a string of [] or None
    **** critvalue - string repr of a number, empty string, or None
    **** warnvalue - string repr of a number, empty string, or None
    **** label - string same as the key
    **** maxvalue - string repr of a number, empty string, or None
    **** minvalue - string repr of a number, empty string, or None
    **** minvalue - string repr of a number

    Here's an example:
    {'command': '/opt/local/libexec/nagios/check_ping -H localhost -w 1,99% -c 1,99%',
     'decoded': {'human': 'PING OK - Packet loss = 0%, RTA = 0.11 ms',
                 'pl': {'UOM': '%',
                        'critvalue': '99',
                        'label': 'pl',
                        'maxvalue': '',
                        'minvalue': '0',
                        'value': '0',
                        'warnvalue': '99'},
                 'rta': {'UOM': 'ms',
                         'critvalue': '1.000000',
                         'label': 'rta',
                         'maxvalue': '',
                         'minvalue': '0.000000',
                         'value': '0.113000',
                         'warnvalue': '1.000000'}},
     'error': None,
     'output': 'PING OK - Packet loss = 0%, RTA = 0.11 ms|rta=0.113000ms;1.000000;1.000000;0.000000 pl=0%;99;99;0',
     'returncode': 0,
     'timestamp': '2009-11-07T16:43:46.696214'}
    """
    UOM_PARSECODE = re.compile('([\d\.]+)([a-zA-Z%]*)')

    def __init__(self):
        self._initialize()
    # def __delitem__(self,key):
    #     del self._internal_dict[key]
    # def __setitem__(self,key,item):
    #     self._internal_dict[key]=item
    # def __getitem__(self,key):
    #     return self._internal_dict[key]
    # def __iter__(self):
    #     return self._internal_dict.__iter__()
    # def __repr__(self):
    #     return self._internal_dict.__repr__()
    # def has_key(self,key):
    #     return self._internal_dict.has_key(key)
    # def keys(self):
    #     return self._internal_dict.keys()

    def _initialize(self):
        self.command = ""
        self.output = ""
        self.error = ""
        self.returncode = 0
        self.timestamp = datetime.datetime.now()
        decoded_dict = {'human': ''}
        empty_label = '_'
        data_dict = {}
        data_dict['label'] = empty_label
        data_dict['value'] = 0
        data_dict['UOM'] = ''
        data_dict['warnvalue'] = ''
        data_dict['critvalue'] = ''
        data_dict['minvalue'] = ''
        data_dict['maxvalue'] = ''
        decoded_dict[empty_label] = data_dict
        self.decoded = decoded_dict

    @staticmethod
    def parse_nagios_output(nagios_output_string):
        """ parses the standard output of a nagios check command. The resulting dictionary as output
        will have at least one key: "human", indicating the human readable portion of what was parsed.
        There will be additional dictionaries of parsed data, each from a key based on the label of
        the performance data returned by the nagios check command.

        For notes on the guidelines for writing Nagios plugins and their expected output, see
        http://nagiosplug.sourceforge.net/developer-guidelines.html

        For example parse_nagios_output("PING OK - Packet loss = 0%, RTA = 0.18 ms|rta=0.182ms;1.00;1.00;0.00 pl=0%;99;99;0")
        should come back as
        {'human': 'PING OK - Packet loss = 0%, RTA = 0.18 ms',
         'pl': {'UOM': '%',
                'critvalue': '99',
                'label': 'pl',
                'maxvalue': '',
                'minvalue': '0',
                'value': '0',
                'warnvalue': '99'},
         'rta': {'UOM': 'ms',
                 'critvalue': '1.00',
                 'label': 'rta',
                 'maxvalue': '',
                 'minvalue': '0.00',
                 'value': '0.182',
                 'warnvalue': '1.00'}}

        Each parsed performance data dictionary should have the following keys:
        * label
        * value
        * UOM
            '' - assume a number (int or float) of things (eg, users, processes, load averages)
            s - seconds (also us, ms)
            % - percentage
            B - bytes (also KB, MB, TB)
            c - a continous counter (such as bytes transmitted on an interface)
        * warnvalue (content may be None)
        * critvalue (content may be None)
        * minvalue (content may be None)
        * maxvalue (content may be None)
        """
        if nagios_output_string is None:
            return None
        return_dict = {}
        try:
            (humandata, parsedata) = nagios_output_string.split('|')
        except ValueError:  # output not in expected format, bail out
            return None
        return_dict['human'] = humandata
        list_of_parsedata = parsedata.split()  # ['rta=0.182000ms;1.000000;1.000000;0.000000', 'pl=0%;99;99;0']
        for dataset in list_of_parsedata:
            parts = dataset.split(';', 5)
            if (len(parts) > 0):
                data_dict = {}
                try:
                    (label, uom_value) = parts[0].split('=')
                except ValueError:  # output not in expected format, bail out
                    return None
                data_dict['label'] = label
                result = MonitorResult.UOM_PARSECODE.match(uom_value)
                data_dict['value'] = result.groups()[0]
                data_dict['UOM'] = result.groups()[1]
                data_dict['warnvalue'] = ''
                data_dict['critvalue'] = ''
                data_dict['minvalue'] = ''
                data_dict['maxvalue'] = ''
                if len(parts) > 1:
                    data_dict['warnvalue'] = parts[1]
                if len(parts) > 2:
                    data_dict['critvalue'] = parts[2]
                if len(parts) > 3:
                    data_dict['minvalue'] = parts[3]
                if len(parts) > 4:
                    data_dict['maxvalue'] = parts[4]
                return_dict[label] = data_dict
        return return_dict

    @staticmethod
    def createMonitorResultFromNagios(nagios_output_string):
        """ creates a new MonitorResult object from a nagios output string """
        if nagios_output_string is None:
            raise ValueError("Empty nagios output string provided to initializer")
        parsed_dict = MonitorResult.parse_nagios_output(nagios_output_string)
        if parsed_dict is None:
            raise ValueError("Error parsing Nagios output")
        new_monitor_result = MonitorResult()
        new_monitor_result.decoded = parsed_dict
        return new_monitor_result

    def json(self):
        """ return MonitorResult as a JSON representation """
        dict_to_dump = {}
        dict_to_dump['command'] = self.command
        dict_to_dump['output'] = self.output
        dict_to_dump['error'] = self.error
        dict_to_dump['returncode'] = self.returncode
        dict_to_dump['timestamp'] = self.timestamp.isoformat()
        dict_to_dump['decoded'] = self.decoded
        return simplejson.dumps(dict_to_dump)

    # unicode_type = type(u'123')
    # string_type = type('123')
    # int_type = type(5)
    # dict_type = type({})
    # list_type = type([])
    # load using "isinstance" if isinstance(key,unicode_type...)

    def loadjson(self, json_string):
        """ load up an external JSON string into an ArgSet, overwriting the existing data here"""
        some_structure = simplejson.loads(json_string)
        # validate structure
        if not(isinstance(some_structure, type({}))):
            raise ValueError("json structure being loaded (%s) is not a dictionary" % some_structure)
        #
        # command validation
        if not('command' in some_structure):
            raise KeyError("dictionary must have a 'command' key")
        new_command = some_structure['command']
        if not(isinstance(new_command, type('123')) or isinstance(new_command, type(u'123'))):
            raise ValueError("command value must be a string or unicode")
        #
        # error validaton
        if not('error' in some_structure):
            raise KeyError("dictionary must have an 'error' key")
        new_error = some_structure['error']
        #
        # return code validaton
        if not('returncode' in some_structure):
            raise KeyError("dictionary must have a 'returncode' key")
        new_rc = some_structure['returncode']
        if not(isinstance(new_rc, type(5))):
            raise ValueError("returncode must be an integer")
        if ((new_rc < 0) or (new_rc > 3)):
            raise ValueError("returncode must be between 0 and 3")
        #
        # timestamp validation
        if not('timestamp' in some_structure):
            raise KeyError("dictionary must have a 'timestamp' key")
        new_timestamp = dateutil.parser.parse(some_structure['timestamp'])
        #
        # output validation
        if not('output' in some_structure):
            raise KeyError("dictionary must have an 'output' key")
        new_output = some_structure['output']
        #
        # decoded validation
        if not('decoded' in some_structure):
            raise KeyError("dictionary must have a 'decoded' key")
        #
        decoded_dict = some_structure['decoded']
        if not(isinstance(decoded_dict, type({}))):
            raise ValueError("decoded value must be a dictionary")
        if not('human' in decoded_dict):
            raise KeyError("decoded dictionary must have a 'human' key")
        if not(isinstance(decoded_dict['human'], type('123')) or isinstance(decoded_dict['human'], type(u'123'))):
            raise ValueError("value for 'human' key must be a string or unicode")
        #
        keylist = decoded_dict.keys()
        keylist.remove('human')
        if len(keylist) < 1:
            raise KeyError("decoded dictionary must have a key other than 'human' ")
        for key in keylist:
            keydict = decoded_dict[key]
            if not(isinstance(keydict, type({}))):
                raise ValueError("keydict must be a dictionary")
            #
            if not('UOM' in keydict):
                raise ValueError("key dictionary must have a 'UOM' key")
            #
            if not('label' in keydict):
                raise ValueError("key dictionary must have a 'label' key")
            #
            if not('maxvalue' in keydict):
                raise ValueError("key dictionary must have a 'maxvalue' key")
            #
            if not('minvalue' in keydict):
                raise ValueError("key dictionary must have a 'minvalue' key")
            #
            if not('critvalue' in keydict):
                raise ValueError("key dictionary must have a 'critvalue' key")
            #
            if not('warnvalue' in keydict):
                raise ValueError("key dictionary must have a 'warnvalue' key")
            #
            if not('value' in keydict):
                raise ValueError("key dictionary must have a 'value' key")
            floatval = float(keydict['value'])
        #
        # we made it through the validation gauntlet - set the structure into place
        self.command = new_command
        self.output = new_output
        self.error = new_error
        self.returncode = new_rc
        self.timestamp = new_timestamp
        self.decoded = decoded_dict


def validate_return_dictionary(result_struct):
    """
    The returning structure should:
    * be a dictionary with the following mandatory keys:
    ** command - string
    ** error - string or None
    ** returncode - integer
    ** timestamp - string of a datestamp (ISO format)
    ** output - string or None
    ** decoded - a dictionary
    ** decoded must have the following keys:
    *** human - a string
    *** 1 or more other keys, which are strings
    *** for each key other than human, the following keys must exist:
    **** UOM - a string of [] or None
    **** critvalue - string repr of a number, empty string, or None
    **** warnvalue - string repr of a number, empty string, or None
    **** label - string same as the key
    **** maxvalue - string repr of a number, empty string, or None
    **** minvalue - string repr of a number, empty string, or None
    **** minvalue - string repr of a number
    """
    if (result_struct.__class__ == {}.__class__):
        # command validation
        if not('command' in result_struct):
            return False
        if result_struct['command'] is None:
            return False
        if not((result_struct['command'].__class__ == '123'.__class__) or (result_struct['command'].__class__ == u'123'.__class__)):
            return False
        # error validaton
        if not('error' in result_struct):
            return False
        # return code validaton
        if not('returncode' in result_struct):
            return False
        if not((type(result_struct['returncode']) == type(3)) or type(result_struct['returncode']) == type(3.1)):
            return False
        if ((result_struct['returncode'] < 0) or (result_struct['returncode'] > 3)):
            return False
        # timestamp validation
        if not('timestamp' in result_struct):
            return False
        try:
            result = dateutil.parser.parse(result_struct['timestamp'])
        except ValueError:
            return False
        if not('output' in result_struct):
            return False
        if not('decoded' in result_struct):
            return False
        decoded_dict = result_struct['decoded']
        if type(decoded_dict) != type({}):
            return False
        if not('human' in decoded_dict):
            return False
        if len(decoded_dict.keys()) < 2:
            return False
        keylist = decoded_dict.keys()
        keylist.remove('human')
        if len(keylist) < 1:
            return False
        for key in keylist:
            keydict = decoded_dict[key]
            if type(keydict) != type({}):
                return False
            if not('UOM' in keydict):
                return False
            #
            if not('critvalue' in keydict):
                return False
            #
            if not('label' in keydict):
                return False
            #
            if not('maxvalue' in keydict):
                return False
            #
            if not('minvalue' in keydict):
                return False
            #
            if not('warnvalue' in keydict):
                return False
            #
            if not('value' in keydict):
                return False
            try:
                floatval = float(keydict['value'])
            except ValueError:
                return False
        #
        return True
    return False


def validate_poller_results(json_return_dict):
    """ validates a return set from a poller, returning True if the format is acceptable, False if not.
    This methods *expects* a JSON string as input
    """
    if json_return_dict is None:
        return False
    try:
        result_struct = simplejson.loads(json_return_dict)
        return validate_return_dictionary(result_struct)
    except:
        return False


class ArgSet:
    """
    a class representing the set of arguments to pass into a command invocation to trigger a poller.
    Expected to be able to be serialized into a JSON object and back again.
    Suitable for a message that can pass in a queue if needed.
    """
    def __init__(self):
        self._internal_list = []

    def list_of_arguments(self):
        """returns a flat list of arguments"""
        return self._internal_list

    def add_argument(self, argument):
        """method for adding a single argument, such as '--help' to a call"""
        self._internal_list.append(argument)

    def add_argument_pair(self, arg_key, arg_value):
        """method for adding a pair of arguments, such as '-H localhost' to a call"""
        new_string = "%s %s" % (arg_key, arg_value)
        self._internal_list.append(new_string)

    def json(self):
        """ return argset as a JSON representation """
        return simplejson.dumps(self._internal_list)

    def loadjson(self, json_string):
        """ load up an external JSON string into an ArgSet, overwriting the existing data here"""
        structure = simplejson.loads(json_string)
        # validate structure
        if (structure.__class__ == [].__class__):
            # outer shell is a list.. so far, so good
            for argument in structure:
                if (argument.__class__ == '123'.__class__) or (argument.__class__ == u'123'.__class__):
                    #argument is a string
                    pass
                else:
                    raise ValueError("argument (%s) is not a string" % argument)
        else:
            raise ValueError("json structure being loaded (%s) was not a list" % structure)
        self._internal_list = structure

    def __str__(self):
        if len(self._internal_list) < 1:
            return ""
        else:
            return " ".join(self._internal_list)

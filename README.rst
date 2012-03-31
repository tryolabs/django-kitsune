:Version: 
  0.1

:Author:
    Raul Garreta - Tryolabs <raul@tryolabs.com>

:Project Website:
   https://github.com/tryolabs/django-kitsune


***********
Description
***********

A Django Admin app to perform host checks. A control panel will be added to the Admin in order to configure hosts, checks and monitor check results.

********
Features
********

* Hosts
Add hosts to monitor.

* Checks
-Add jobs with checks to be performed
-Schedule
-Check to be performed
-Host to check
-Select users or groups to be notified
-Configure notification rules
-Select how to render results
-Set amount of log history to keep

* Custom Checks
-You can implement your own checks by implementing a subclass of

* Nagios Checks
-A builtin check is provided that wrapps any Nagios check.
-You can use any existing Nagios check within django-kitsune

* Logs
-Log and list check results

* Result Renderers
-Can implement renderers by implementing a subclass of
-Returns a html with the corresponding result that will be rendered within result listings.

* List Checks
-Host name, last time performed, last result, next scheduled run.

* Notification Rules
-Notifications through e-mail.
-Configure who to notify: Groups or Users.
-Configure when to trigger a notification.
-Configure the frequency of notifications to avoid spam emails :)

* All configurations are made through a graphic UI within admin panel.


************
Requirements
************

* Python 2.6 and higher.
* Nagios plugins: `sudo apt-get install nagios-plugins`

************
Installation
************

To install Kitsune:

1. ``easy_install django-kitsune`` or download package and execute `python setup.py install`
2. Add ``'kitsune'`` to the `INSTALLED_APPS` in your project's ``settings.py``

*************
Configuration
*************

Kitsune can be configured via the following parameters, to be defined in your project settings file:

* ``KITSUNE_RENDERERS``: List of modules that contain renderer classes, eg:: ['myproject.myapp.renderers']


***************
Acknowledgments
***************

Kitsune scheduling system is based on django-chronograph. 



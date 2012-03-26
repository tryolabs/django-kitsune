# -*- coding: utf-8 -
'''
Created on Mar 3, 2012

@author: Raul Garreta (raul@tryolabs.com)

Kitsune models.
Based on django-chronograph.

'''

__author__      = "Raul Garreta (raul@tryolabs.com)"


import os
import re
import subprocess
import sys
import traceback
import inspect
from socket import gethostname
from datetime import datetime
from dateutil import rrule
from StringIO import StringIO
from datetime import datetime, timedelta

from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.management import call_command
from django.db import models
from django.template import loader, Context
from django.utils.timesince import timeuntil
from django.utils.translation import ungettext, ugettext, ugettext_lazy as _
from django.utils.encoding import smart_str
from django.core import urlresolvers
from django.template.loader import render_to_string

from kitsune.utils import get_manage_py
from kitsune.renderers import KitsuneJobRenderer
from kitsune.base import STATUS_OK, STATUS_WARNING, STATUS_CRITICAL, STATUS_UNKNOWN
from kitsune.mail import send_mail, send_multi_mail
from kitsune.html2text import html2text


RRULE_WEEKDAY_DICT = {"MO":0,"TU":1,"WE":2,"TH":3,"FR":4,"SA":5,"SU":6}

THRESHOLD_CHOICES = (

    (STATUS_OK, 'Status OK'),
    (STATUS_WARNING, 'Status Warning'),
    (STATUS_CRITICAL, 'Status Critical'),
    (STATUS_UNKNOWN, 'Status Unknown'),
                     
)

RULE_LAST = 'lt'
RULE_LAST_N = 'n_lt'
RULE_LAST_N_M = 'n_m_lt'

REPETITION_CHOICES = (

    (RULE_LAST, 'Last Time'),
    (RULE_LAST_N, 'N last times'),
    (RULE_LAST_N_M, 'M of N last times'),
                     
)


class JobManager(models.Manager):
    def due(self):
        """
        Returns a ``QuerySet`` of all jobs waiting to be run.
        """
        return self.filter(next_run__lte=datetime.now(), disabled=False, is_running=False)

# A lot of rrule stuff is from django-schedule
freqs = (   
            ("YEARLY", _("Yearly")),
            ("MONTHLY", _("Monthly")),
            ("WEEKLY", _("Weekly")),
            ("DAILY", _("Daily")),
            ("HOURLY", _("Hourly")),
            ("MINUTELY", _("Minutely")),
            ("SECONDLY", _("Secondly"))
)


NOTIF_INTERVAL_CHOICES = (
            ("Hours", _("Hours")),
            ("Minutes", _("Minutes")),
)


def get_render_choices():
    choices = []
    try:
        for kls in settings.KITSUNE_RENDERERS:
            __import__(kls)
            m = sys.modules[kls]
            for name, obj in inspect.getmembers(m):
                if inspect.isclass(obj) and issubclass(obj, KitsuneJobRenderer):
                    class_name = kls + '.' + name
                    if name != "KitsuneJobRenderer" and class_name not in choices:
                        choices.append((class_name, class_name))
    except:
        pass
    choices.append(("kitsune.models.KitsuneJobRenderer", "kitsune.models.KitsuneJobRenderer"))
    return choices
    

class Job(models.Model):
    """
    A recurring ``django-admin`` command to be run.
    """
    name = models.CharField(_("name"), max_length=200)
    frequency = models.CharField(_("frequency"), choices=freqs, max_length=10)
    params = models.TextField(_("params"), null=True, blank=True,
        help_text=_('Comma-separated list of <a href="http://labix.org/python-dateutil" target="_blank">rrule parameters</a>. e.g: interval:15'))
    command = models.CharField(_("command"), max_length=200,
        help_text=_("A valid django-admin command to run."), blank=True)
    args = models.CharField(_("args"), max_length=200, blank=True,
        help_text=_("Space separated list; e.g: arg1 option1=True"))
    disabled = models.BooleanField(default=False, help_text=_('If checked this job will never run.'))
    next_run = models.DateTimeField(_("next run"), blank=True, null=True, help_text=_("If you don't set this it will be determined automatically"))
    last_run = models.DateTimeField(_("last run"), editable=False, blank=True, null=True)
    is_running = models.BooleanField(default=False, editable=False)
    last_run_successful = models.BooleanField(default=True, blank=False, null=False, editable=False)
    
    pid = models.IntegerField(blank=True, null=True, editable=False)
    force_run = models.BooleanField(default=False)
    host = models.ForeignKey('Host')
    last_result = models.ForeignKey('Log', related_name='running_job', null=True, blank=True)
    renderer = models.CharField(choices=get_render_choices(), max_length=100, default="kitsune.models.KitsuneJobRenderer")
    last_logs_to_keep = models.PositiveIntegerField(default=20)
    
    
    objects = JobManager()
    
    class Meta:
        ordering = ('disabled', 'next_run',)
    
    def __unicode__(self):
        if self.disabled:
            return _(u"%(name)s - disabled") % {'name': self.name}
        return u"%s - %s" % (self.name, self.timeuntil)
    
    def save(self, force_insert=False, force_update=False):
        if not self.disabled:
            if self.pk:
                j = Job.objects.get(pk=self.pk)
            else:
                j = self
            if not self.next_run or j.params != self.params:
                self.next_run = self.rrule.after(datetime.now())
        else:
            self.next_run = None
        
        super(Job, self).save(force_insert, force_update)

    def get_timeuntil(self):
        """
        Returns a string representing the time until the next
        time this Job will be run.
        """
        if self.disabled:
            return _('never (disabled)')
        
        delta = self.next_run - datetime.now()
        if delta.days < 0:
            # The job is past due and should be run as soon as possible
            return _('due')
        elif delta.seconds < 60:
            # Adapted from django.utils.timesince
            count = lambda n: ungettext('second', 'seconds', n)
            return ugettext('%(number)d %(type)s') % {'number': delta.seconds,
                                                      'type': count(delta.seconds)}
        return timeuntil(self.next_run)
    get_timeuntil.short_description = _('time until next run')
    timeuntil = property(get_timeuntil)
    
    def get_rrule(self):
        """
        Returns the rrule objects for this Job.
        """
        frequency = eval('rrule.%s' % self.frequency)
        return rrule.rrule(frequency, dtstart=self.last_run, **self.get_params())
    rrule = property(get_rrule)

    def param_to_int(self, param_value):
        """
        Converts a valid rrule parameter to an integer if it is not already one, else
        raises a ``ValueError``.  The following are equivalent:
        
            >>> job = Job(params = "byweekday:1,2,4,5")
            >>> job = Job(params = "byweekday:TU,WE,FR,SA")
        """
        if param_value in RRULE_WEEKDAY_DICT:
            return RRULE_WEEKDAY_DICT[param_value]
        try:
            val = int(param_value)
        except ValueError:
            raise ValueError('rrule parameter should be integer or weekday constant (e.g. MO, TU, etc.).  Error on: %s' % param_value)
        else:
            return val
    
    def get_params(self):
        """
        >>> job = Job(params = "count:1;bysecond:1;byminute:1,2,4,5")
        >>> job.get_params()
        {'count': 1, 'byminute': [1, 2, 4, 5], 'bysecond': 1}
        """
        if self.params is None:
            return {}
        params = self.params.split(';')
        param_dict = []
        for param in params:
            if param.strip() == "":
                continue # skip blanks
            param = param.split(':')
            if len(param) == 2:
                param = (str(param[0]).strip(), [self.param_to_int(p.strip()) for p in param[1].split(',')])
                if len(param[1]) == 1:
                    param = (param[0], param[1][0])
                param_dict.append(param)
        return dict(param_dict)
    
    def get_args(self):
        """
        Processes the args and returns a tuple or (args, options) for passing to ``call_command``.
        """
        args = []
        options = {}
        for arg in self.args.split():
            if arg.find('=') > -1:
                key, value = arg.split('=')
                options[smart_str(key)] = smart_str(value)
            else:
                args.append(arg)
        return (args, options)
    
    def is_due(self):
        reqs =  (self.next_run <= datetime.now() and self.disabled == False 
                and self.is_running == False)
        return (reqs or self.force_run)
    
    def run(self, wait=True):
        """
        Runs this ``Job``.  If ``wait`` is ``True`` any call to this function will not return
        untill the ``Job`` is complete (or fails).  This actually calls the management command
        ``kitsune_run_job`` via a subprocess.  If you call this and want to wait for the process to
        complete, pass ``wait=True``.
        
        A ``Log`` will be created if there is any output from either stdout or stderr.
        
        Returns the process, a ``subprocess.Popen`` instance, or None.
        """
        if not self.disabled and self.host.name == gethostname():
            if not self.check_is_running() and self.is_due():
                p = subprocess.Popen(['python', get_manage_py(), 'kitsune_run_job', str(self.pk)])
                if wait:
                    p.wait()
                return p
        return None
    
    def handle_run(self):
        """
        This method implements the code to actually run a job.  This is meant to be run, primarily,
        by the `kitsune_run_job` management command as a subprocess, which can be invoked by calling
        this job's ``run_job`` method.
        """     
        args, options = self.get_args()
        stdout = StringIO()
        stderr = StringIO()

        # Redirect output so that we can log it if there is any
        ostdout = sys.stdout
        ostderr = sys.stderr
        sys.stdout = stdout
        sys.stderr = stderr
        stdout_str, stderr_str = "", ""

        run_date = datetime.now()
        self.is_running = True
        self.pid = os.getpid()
        self.save()
        
        try:
            call_command(self.command, *args, **options)
            self.last_run_successful = True
        except Exception, e:
            # The command failed to run; log the exception
            t = loader.get_template('kitsune/error_message.txt')
            c = Context({
              'exception': unicode(e),
              'traceback': ['\n'.join(traceback.format_exception(*sys.exc_info()))]
            })
            stderr_str += t.render(c)
            self.last_run_successful = False
        
        self.is_running = False
        self.pid = None
        self.last_run = run_date
        
        # If this was a forced run, then don't update the
        # next_run date
        if self.force_run:
            self.force_run = False
        else:
            self.next_run = self.rrule.after(run_date)
        
        # If we got any output, save it to the log
        stdout_str += stdout.getvalue()
        stderr_str += stderr.getvalue()
        
        if stderr_str:
            # If anything was printed to stderr, consider the run
            # unsuccessful
            self.last_run_successful = False
        
        if stdout_str or stderr_str:
            log = Log.objects.create(
                job = self,
                run_date = run_date,
                stdout = stdout_str,
                stderr = stderr_str
            )
            self.last_result = log
        
        self.save()
        
        self.delete_old_logs()
        
        self.email_subscribers()

        # Redirect output back to default
        sys.stdout = ostdout
        sys.stderr = ostderr
        
        
    def email_subscribers(self):
        from_email = settings.DEFAULT_FROM_EMAIL
        subject = 'Kitsune monitoring notification'
        
        user_ids = set([])
        for sub in self.subscriber_users.all():
            #notify subscribed users
            if sub.must_notify():
                sub.last_notification = datetime.now()
                sub.save()
                html_message = render_to_string('kitsune/mail_notification.html', {'log':self.last_result})
                text_message = html2text(html_message)
                user_ids.add(sub.user.id)
                send_multi_mail(subject,text_message,html_message,from_email,[sub.user.email],fail_silently=False)
        
        for sub in self.subscriber_groups.all():
            if sub.must_notify():
                #notify subscribed groups
                sub.last_notification = datetime.now()
                sub.save()
                for user in sub.group.user_set.all():
                    if not (user.id in user_ids):
                        #notify users that have not already being notified
                        html_message = render_to_string('kitsune/mail_notification.html', {'log':self.last_result})
                        text_message = html2text(html_message)
                        send_multi_mail(subject,text_message,html_message,from_email,[user.email],fail_silently=False)
        
        
    def delete_old_logs(self):
        log = Log.objects.filter(job=self).order_by('-run_date')[self.last_logs_to_keep]
        Log.objects.filter(job=self, run_date__lte=log.run_date).delete()
    
    def check_is_running(self):
        """
        This function actually checks to ensure that a job is running.
        Currently, it only supports `posix` systems.  On non-posix systems
        it returns the value of this job's ``is_running`` field.
        """
        status = False
        if self.is_running and self.pid is not None:
            # The Job thinks that it is running, so
            # lets actually check
            if os.name == 'posix':
                # Try to use the 'ps' command to see if the process
                # is still running
                pid_re = re.compile(r'%d ([^\r\n]*)\n' % self.pid)
                p = subprocess.Popen(["ps", "-eo", "pid args"], stdout=subprocess.PIPE)
                p.wait()
                # If ``pid_re.findall`` returns a match it means that we have a
                # running process with this ``self.pid``.  Now we must check for
                # the ``run_command`` process with the given ``self.pk``
                try:
                    pname = pid_re.findall(p.stdout.read())[0]
                except IndexError:
                    pname = ''
                if pname.find('kitsune_run_job %d' % self.pk) > -1:
                    # This Job is still running
                    return True
                else:
                    # This job thinks it is running, but really isn't.
                    self.is_running = False
                    self.pid = None
                    self.save()
            else:
                # TODO: add support for other OSes
                return self.is_running
        return False
    

class NotificationRule(models.Model):
    last_notification = models.DateTimeField(blank=True, null=True, editable=False)
    threshold = models.IntegerField(choices=THRESHOLD_CHOICES, max_length=10)
    rule_type = models.CharField(choices=REPETITION_CHOICES, max_length=10)
    rule_N = models.PositiveIntegerField(default=1)
    rule_M = models.PositiveIntegerField(default=2)
    interval_unit = models.CharField(choices=NOTIF_INTERVAL_CHOICES, max_length=10)
    interval_value = models.PositiveIntegerField(default=1)
    enabled = models.BooleanField(default=True)
    
    def __unicode__(self):
        return u'Notification to:'
    
    def must_notify(self):
        if self.enabled:
            
            if self.last_notification is not None:
                if self.interval_unit == 'Minutes':
                    dt = timedelta(minutes=self.interval_value)
                elif self.interval_unit == 'Hours':
                    dt = timedelta(hours=self.interval_value)
                else:
                    dt = timedelta(hours=1)
                
                threshold = self.last_notification + dt  
                tt = datetime.now()   
                if threshold > tt:
                    return False
            
            if self.rule_type == RULE_LAST:
                return self.job.last_result.get_status_code() >= self.threshold
                    
            elif self.rule_type == RULE_LAST_N:
                n = 0
                logs = self.job.logs.order_by('-run_date')[:self.rule_N]
                for log in logs:
                    if log.get_status_code() < self.threshold:
                        break
                    else:
                        n += 1
                return n == self.rule_N
                    
            elif self.rule_type == RULE_LAST_N_M:
                n = 0
                logs = self.job.logs.order_by('-run_date')[:self.rule_N]
                for log in logs:
                    if log.get_status_code() >= self.threshold:
                        n += 1
                return n >= self.rule_M
        return False
    
    class Meta:
        abstract = True
    
    
class NotificationUser(NotificationRule):
    job = models.ForeignKey('Job', related_name='subscriber_users')
    user = models.ForeignKey(User)
    
    
class NotificationGroup(NotificationRule):
    job = models.ForeignKey('Job', related_name='subscriber_groups')
    group = models.ForeignKey(Group)
       

class Log(models.Model):
    """
    A record of stdout and stderr of a ``Job``.
    """
    job = models.ForeignKey('Job', related_name='logs')
    run_date = models.DateTimeField(auto_now_add=True)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    success = models.BooleanField(default=True)#, editable=False)
        
    class Meta:
        ordering = ('-run_date',)
    
    def __unicode__(self):
        return u"%s - %s" % (self.job.name, self.run_date)

    def admin_link(self):
        return urlresolvers.reverse('admin:kitsune_' + self.__class__.__name__.lower() + '_change', args=(self.id,))
    
    def get_status_code(self):
        return int(self.stderr)


class Host(models.Model):
    """
    The hosts to be checked.
    """
    name = models.CharField(blank=False, max_length=150)
    ip = models.CharField(blank=True, max_length=15)
    description = models.TextField(blank=True)
    
    def __unicode__(self):
        return self.name
    
    

    
    
    
    

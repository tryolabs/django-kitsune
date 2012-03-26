# -*- coding: utf-8 -
'''
Created on Mar 3, 2012

@author: Raul Garreta (raul@tryolabs.com)

Admin interface.
Based on django-chronograph.

'''

__author__      = "Raul Garreta (raul@tryolabs.com)"


import sys
import inspect
import pkgutil
import os.path
from datetime import datetime

from django import forms
from django.conf.urls.defaults import patterns, url
from django.contrib import admin
from django.core.management import get_commands
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db import models
from django.forms.util import flatatt
from django.http import HttpResponseRedirect, Http404
from django.template.defaultfilters import linebreaks
from django.utils import dateformat
from django.utils.datastructures import MultiValueDict
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ungettext, get_date_formats, ugettext_lazy as _
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

from kitsune.models import Job, Log, Host, NotificationUser, NotificationGroup
from kitsune.renderers import STATUS_OK, STATUS_WARNING, STATUS_CRITICAL, STATUS_UNKNOWN
from kitsune.base import BaseKitsuneCheck
 

def get_class(kls):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m

class HTMLWidget(forms.Widget):
    def __init__(self,rel=None, attrs=None):
        self.rel = rel
        super(HTMLWidget, self).__init__(attrs)
    
    def render(self, name, value, attrs=None):
        if self.rel is not None:
            key = self.rel.get_related_field().name
            obj = self.rel.to._default_manager.get(**{key: value})
            related_url = '../../../%s/%s/%d/' % (self.rel.to._meta.app_label, self.rel.to._meta.object_name.lower(), value)
            value = "<a href='%s'>%s</a>" % (related_url, escape(obj))
            
        final_attrs = self.build_attrs(attrs, name=name)
        return mark_safe("<div%s>%s</div>" % (flatatt(final_attrs), linebreaks(value)))

class NotificationUserInline(admin.TabularInline):
    model = NotificationUser
    extra = 1
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(is_staff=True)
        return super(NotificationUserInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    
class NotificationGroupInline(admin.TabularInline):
    model = NotificationGroup
    extra = 1
    
#from django.contrib.admin import SimpleListFilter
#
#class StatusCodeListFilter(SimpleListFilter):
#    # Human-readable title which will be displayed in the
#    # right admin sidebar just above the filter options.
#    title = _('status_code')
#
#    # Parameter for the filter that will be used in the URL query.
#    parameter_name = 'status_code'
#
#    def lookups(self, request, model_admin):
#        """
#        Returns a list of tuples. The first element in each
#        tuple is the coded value for the option that will
#        appear in the URL query. The second element is the
#        human-readable name for the option that will appear
#        in the right sidebar.
#        """
#        return (
#            ('0', _('OK')),
#            ('1', _('WARNING')),
#            ('2', _('ERROR')),
#            ('3', _('UNKNOWN')),
#        )
#
#    def queryset(self, request, queryset):
#        """
#        Returns the filtered queryset based on the value
#        provided in the query string and retrievable via
#        `self.value()`.
#        """
#        # Compare the requested value (either '80s' or 'other')
#        # to decide how to filter the queryset.
#        return queryset.filter(last_result__stderr=self.value())

    
class JobAdmin(admin.ModelAdmin):
    inlines = (NotificationUserInline, NotificationGroupInline)
    actions = ['run_selected_jobs']
    list_display = ('name', 'host', 'last_run_with_link', 'get_timeuntil',
                    'get_frequency',  'is_running', 'run_button', 'view_logs_button', 'status_code', 'status_message')
    list_display_links = ('name', )
    list_filter = ('host',)
    fieldsets = (
        ('Job Details', {
            'classes': ('wide',),
            'fields': ('name', 'host', 'command', 'args', 'disabled', 'renderer')
        }),
        ('Scheduling options', {
            'classes': ('wide',),
            'fields': ('frequency', 'next_run', 'params',)
        }),
        ('Log options', {
            'classes': ('wide',),
            'fields': ('last_logs_to_keep',)
        }),     
    )
    search_fields = ('name', )
    
    def last_run_with_link(self, obj):
        format = get_date_formats()[1]
        value = capfirst(dateformat.format(obj.last_run, format))
        
        try:
            log_id = obj.log_set.latest('run_date').id
            try:
                # Old way
                url = reverse('kitsune_log_change', args=(log_id,))
            except NoReverseMatch:
                # New way
                url = reverse('admin:kitsune_log_change', args=(log_id,))
            return '<a href="%s">%s</a>' % (url, value)
        except:
            return value
    last_run_with_link.admin_order_field = 'last_run'
    last_run_with_link.allow_tags = True
    last_run_with_link.short_description = 'Last run'
    
    def get_timeuntil(self, obj):
        format = get_date_formats()[1]
        value = capfirst(dateformat.format(obj.next_run, format))
        return "%s<br /><span class='mini'>(%s)</span>" % (value, obj.get_timeuntil())
    get_timeuntil.admin_order_field = 'next_run'
    get_timeuntil.allow_tags = True
    get_timeuntil.short_description = _('next scheduled run')
    
    def get_frequency(self, obj):
        freq = capfirst(obj.frequency.lower())
        if obj.params:
            return "%s (%s)" % (freq, obj.params)
        return freq
    get_frequency.admin_order_field = 'frequency'
    get_frequency.short_description = 'Frequency'
    
    def run_button(self, obj):
        on_click = "window.location='%d/run/?inline=1';" % obj.id
        return '<input type="button" onclick="%s" value="Run" />' % on_click
    run_button.allow_tags = True
    run_button.short_description = 'Run'
    
    def status_code(self, obj):
        if obj.last_result is not None:
            Renderer = get_class(obj.renderer)
            return Renderer().get_html_status(obj.last_result)
        else:
            return '--'
    status_code.allow_tags = True
    status_code.short_description = 'Status Code'
    
    def status_message(self, obj):
        if obj.last_result is not None:
            Renderer = get_class(obj.renderer)
            return '<a href=' + obj.last_result.admin_link() + '>' + Renderer().get_html_message(obj.last_result) + '</a>'
        else:
            return '--'
    status_message.allow_tags = True
    status_message.short_description = 'Status Message'
        
    def view_logs_button(self, obj):
        on_click = "window.location='../log/?job=%d';" % obj.id
        return '<input type="button" onclick="%s" value="View Logs" />' % on_click
    view_logs_button.allow_tags = True
    view_logs_button.short_description = 'Logs'
    
    def run_job_view(self, request, pk):
        """
        Runs the specified job.
        """
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            raise Http404
        # Rather than actually running the Job right now, we
        # simply force the Job to be run by the next cron job
        job.force_run = True
        job.save()
        request.user.message_set.create(message=_('The job "%(job)s" has been scheduled to run.') % {'job': job})        
        if 'inline' in request.GET:
            redirect = request.path + '../../'
        else:
            redirect = request.REQUEST.get('next', request.path + "../")
        return HttpResponseRedirect(redirect)
    
    def get_urls(self):
        urls = super(JobAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^(.+)/run/$', self.admin_site.admin_view(self.run_job_view), name="kitsune_job_run")
        )
        return my_urls + urls
    
    def run_selected_jobs(self, request, queryset):
        rows_updated = queryset.update(next_run=datetime.now())
        if rows_updated == 1:
            message_bit = "1 job was"
        else:
            message_bit = "%s jobs were" % rows_updated
        self.message_user(request, "%s successfully set to run." % message_bit)
    run_selected_jobs.short_description = "Run selected jobs"
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        request = kwargs.pop("request", None)
        
        # Add a select field of available commands
        if db_field.name == 'command':
            choices_dict = MultiValueDict()
            #l = get_commands().items():
            #l = [('kitsune_base_check', 'kitsune')]
            l = get_kitsune_checks()
            for command, app in l:
                choices_dict.appendlist(app, command)
            
            choices = []
            for key in choices_dict.keys():
                #if str(key).startswith('<'):
                #    key = str(key)
                commands = choices_dict.getlist(key)
                commands.sort()
                choices.append([key, [[c,c] for c in commands]])
                
            kwargs['widget'] = forms.widgets.Select(choices=choices)
            return db_field.formfield(**kwargs)
        kwargs['request'] = request    
        return super(JobAdmin, self).formfield_for_dbfield(db_field, **kwargs)


def get_kitsune_checks():
    
    # Find the installed apps
    try:
        from django.conf import settings
        apps = settings.INSTALLED_APPS
    except (AttributeError, EnvironmentError, ImportError):
        apps = []

    paths = []
    choices = []
    
    for app in apps:
        paths.append((app, app + '.management.commands'))

    for app, package in paths:
        try:
            __import__(package)
            m = sys.modules[package]
            path = os.path.dirname(m.__file__)
            for _, name, _ in pkgutil.iter_modules([path]):
                pair = (name, app)
                __import__(package + '.' + name)
                m2 = sys.modules[package + '.' + name]
                for _, obj in inspect.getmembers(m2):
                    if inspect.isclass(obj) and issubclass(obj, BaseKitsuneCheck) and issubclass(obj, BaseCommand):
                        if not pair in choices:
                            choices.append(pair)
        except:
            pass
    return choices


class LogAdmin(admin.ModelAdmin):
    list_display = ('job_name', 'run_date', 'job_success', 'output', 'errors', )
    search_fields = ('stdout', 'stderr', 'job__name', 'job__command')
    date_hierarchy = 'run_date'
    fieldsets = (
        (None, {
            'fields': ('job',)
        }),
        ('Output', {
            'fields': ('stdout', 'stderr',)
        }),
    )
    
    def job_name(self, obj):
        return obj.job.name
    job_name.short_description = _(u'Name')

    def job_success(self, obj):
        return obj.success
    job_success.short_description = _(u'OK')
    job_success.boolean = True

    def output(self, obj):
        if obj.stdout is not None and obj.stdout != '':
            Renderer = get_class(obj.job.renderer)
            return Renderer().get_html_message(obj)
        else:
            return '--'
    output.allow_tags = True
    
    def errors(self, obj):
        if obj.stderr is not None:
            Renderer = get_class(obj.job.renderer)
            return Renderer().get_html_status(obj)
        else:
            return '--'
    errors.allow_tags = True
    
    def has_add_permission(self, request):
        return False
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        request = kwargs.pop("request", None)
        
        if isinstance(db_field, models.TextField):
            kwargs['widget'] = HTMLWidget()
            return db_field.formfield(**kwargs)
        
        if isinstance(db_field, models.ForeignKey):
            kwargs['widget'] = HTMLWidget(db_field.rel)
            return db_field.formfield(**kwargs)
        
        return super(LogAdmin, self).formfield_for_dbfield(db_field, **kwargs)

try:
    admin.site.register(Job, JobAdmin)
except admin.sites.AlreadyRegistered:
    pass

admin.site.register(Log, LogAdmin)
#admin.site.register(Log)
admin.site.register(Host)




    
    
    

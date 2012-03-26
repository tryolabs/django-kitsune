# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'NotificationRule'
        db.delete_table('kitsune_notificationrule')

        # Adding model 'NotificationGroup'
        db.create_table('kitsune_notificationgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('last_notification', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('threshold', self.gf('django.db.models.fields.IntegerField')(max_length=10)),
            ('rule_type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('rule_N', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('rule_M', self.gf('django.db.models.fields.PositiveIntegerField')(default=2)),
            ('interval_unit', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('interval_value', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('job', self.gf('django.db.models.fields.related.ForeignKey')(related_name='subscriber_groups', to=orm['kitsune.Job'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'])),
        ))
        db.send_create_signal('kitsune', ['NotificationGroup'])

        # Adding model 'NotificationUser'
        db.create_table('kitsune_notificationuser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('last_notification', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('threshold', self.gf('django.db.models.fields.IntegerField')(max_length=10)),
            ('rule_type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('rule_N', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('rule_M', self.gf('django.db.models.fields.PositiveIntegerField')(default=2)),
            ('interval_unit', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('interval_value', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('job', self.gf('django.db.models.fields.related.ForeignKey')(related_name='subscriber_users', to=orm['kitsune.Job'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('kitsune', ['NotificationUser'])


    def backwards(self, orm):
        
        # Adding model 'NotificationRule'
        db.create_table('kitsune_notificationrule', (
            ('interval_unit', self.gf('django.db.models.fields.CharField')(default='Hours', max_length=10)),
            ('job', self.gf('django.db.models.fields.related.ForeignKey')(related_name='subscribers', to=orm['kitsune.Job'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('threshold', self.gf('django.db.models.fields.IntegerField')(max_length=10)),
            ('last_notification', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rule_type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('interval_value', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('rule_M', self.gf('django.db.models.fields.PositiveIntegerField')(default=2)),
            ('rule_N', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('kitsune', ['NotificationRule'])

        # Deleting model 'NotificationGroup'
        db.delete_table('kitsune_notificationgroup')

        # Deleting model 'NotificationUser'
        db.delete_table('kitsune_notificationuser')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'kitsune.host': {
            'Meta': {'object_name': 'Host'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        'kitsune.job': {
            'Meta': {'ordering': "('disabled', 'next_run')", 'object_name': 'Job'},
            'args': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'command': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'force_run': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'frequency': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['kitsune.Host']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_running': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_logs_to_keep': ('django.db.models.fields.PositiveIntegerField', [], {'default': '20'}),
            'last_result': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'running_job'", 'null': 'True', 'to': "orm['kitsune.Log']"}),
            'last_run': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_run_successful': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'next_run': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'params': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'pid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'renderer': ('django.db.models.fields.CharField', [], {'default': "'kitsune.models.KitsuneJobRenderer'", 'max_length': '100'})
        },
        'kitsune.log': {
            'Meta': {'ordering': "('-run_date',)", 'object_name': 'Log'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': "orm['kitsune.Job']"}),
            'run_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'stderr': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'stdout': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'success': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'kitsune.notificationgroup': {
            'Meta': {'object_name': 'NotificationGroup'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval_unit': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'interval_value': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subscriber_groups'", 'to': "orm['kitsune.Job']"}),
            'last_notification': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'rule_M': ('django.db.models.fields.PositiveIntegerField', [], {'default': '2'}),
            'rule_N': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'rule_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'threshold': ('django.db.models.fields.IntegerField', [], {'max_length': '10'})
        },
        'kitsune.notificationuser': {
            'Meta': {'object_name': 'NotificationUser'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval_unit': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'interval_value': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subscriber_users'", 'to': "orm['kitsune.Job']"}),
            'last_notification': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'rule_M': ('django.db.models.fields.PositiveIntegerField', [], {'default': '2'}),
            'rule_N': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'rule_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'threshold': ('django.db.models.fields.IntegerField', [], {'max_length': '10'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['kitsune']

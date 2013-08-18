# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Player'
        db.create_table('website_player', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('player_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('player_key', self.gf('django.db.models.fields.CharField')(max_length=32, primary_key=True)),
            ('position_type', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('uniform_number', self.gf('django.db.models.fields.IntegerField')()),
            ('image_url', self.gf('django.db.models.fields.TextField')()),
            ('headshot_url', self.gf('django.db.models.fields.TextField')()),
            ('is_undroppable', self.gf('django.db.models.fields.IntegerField')()),
            ('display_position', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('editorial_player_key', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('editorial_team_full_name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('editorial_team_key', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('eligible_positions', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('bye_week', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('website', ['Player'])

        # Adding model 'PlayerStat'
        db.create_table('website_playerstat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('week', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('season', self.gf('django.db.models.fields.IntegerField')(default=2013)),
            ('player', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['website.Player'])),
            ('stat_id', self.gf('django.db.models.fields.IntegerField')()),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('website', ['PlayerStat'])

        # Adding model 'GoogleCredential'
        db.create_table('website_googlecredential', (
            ('token_expiry', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 8, 17, 0, 0))),
            ('access_token', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('token_uri', self.gf('django.db.models.fields.URLField')(default='https://accounts.google.com/o/oauth2/token', max_length=200)),
            ('invalid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('token_type', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('expires_in', self.gf('django.db.models.fields.IntegerField')()),
            ('client_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('client_secret', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('revoke_uri', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('user_agent', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], primary_key=True)),
            ('refresh_token', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal('website', ['GoogleCredential'])


    def backwards(self, orm):
        # Deleting model 'Player'
        db.delete_table('website_player')

        # Deleting model 'PlayerStat'
        db.delete_table('website_playerstat')

        # Deleting model 'GoogleCredential'
        db.delete_table('website_googlecredential')


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
        'website.googlecredential': {
            'Meta': {'object_name': 'GoogleCredential'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'client_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'client_secret': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'expires_in': ('django.db.models.fields.IntegerField', [], {}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'refresh_token': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'revoke_uri': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'token_expiry': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 8, 17, 0, 0)'}),
            'token_type': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'token_uri': ('django.db.models.fields.URLField', [], {'default': "'https://accounts.google.com/o/oauth2/token'", 'max_length': '200'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'primary_key': 'True'}),
            'user_agent': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'website.player': {
            'Meta': {'object_name': 'Player'},
            'bye_week': ('django.db.models.fields.IntegerField', [], {}),
            'display_position': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'editorial_player_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'editorial_team_full_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'editorial_team_key': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'eligible_positions': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'headshot_url': ('django.db.models.fields.TextField', [], {}),
            'image_url': ('django.db.models.fields.TextField', [], {}),
            'is_undroppable': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'player_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'player_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'position_type': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'uniform_number': ('django.db.models.fields.IntegerField', [], {})
        },
        'website.playerstat': {
            'Meta': {'object_name': 'PlayerStat'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'player': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['website.Player']"}),
            'season': ('django.db.models.fields.IntegerField', [], {'default': '2013'}),
            'stat_id': ('django.db.models.fields.IntegerField', [], {}),
            'value': ('django.db.models.fields.IntegerField', [], {}),
            'week': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['website']
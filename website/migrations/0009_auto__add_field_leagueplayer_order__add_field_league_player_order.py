# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'LeaguePlayer.order'
        db.add_column('website_leagueplayer', 'order',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'League.player_order'
        db.add_column('website_league', 'player_order',
                      self.gf('django.db.models.fields.TextField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'LeaguePlayer.order'
        db.delete_column('website_leagueplayer', 'order')

        # Deleting field 'League.player_order'
        db.delete_column('website_league', 'player_order')


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
            'token_expiry': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 8, 28, 0, 0)'}),
            'token_type': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'token_uri': ('django.db.models.fields.URLField', [], {'default': "'https://accounts.google.com/o/oauth2/token'", 'max_length': '200'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'google_credential'", 'primary_key': 'True', 'to': "orm['auth.User']"}),
            'user_agent': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'website.league': {
            'Meta': {'object_name': 'League'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'league_type': ('django.db.models.fields.CharField', [], {'default': "'ESPN'", 'max_length': '32'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'League'", 'max_length': '64'}),
            'player_order': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'players': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['website.Player']", 'through': "orm['website.LeaguePlayer']", 'symmetrical': 'False'}),
            'record': ('django.db.models.fields.CharField', [], {'default': "'0 - 0'", 'max_length': '32'}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'})
        },
        'website.leagueplayer': {
            'Meta': {'unique_together': "(('league', 'player'),)", 'object_name': 'LeaguePlayer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'league': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['website.League']"}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'player': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['website.Player']"})
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
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'player_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'player_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'position_type': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'times_updates': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'uniform_number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'website.playerstat': {
            'Meta': {'unique_together': "(('week', 'season', 'player', 'stat_id'),)", 'object_name': 'PlayerStat'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'player': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stats'", 'to': "orm['website.Player']"}),
            'season': ('django.db.models.fields.IntegerField', [], {'default': '2013'}),
            'stat_id': ('django.db.models.fields.IntegerField', [], {}),
            'value': ('django.db.models.fields.IntegerField', [], {}),
            'week': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'website.userleague': {
            'Meta': {'unique_together': "(('league', 'user_profile'),)", 'object_name': 'UserLeague'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'league': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['website.League']"}),
            'user_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['website.UserProfile']"})
        },
        'website.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'leagues': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['website.League']", 'through': "orm['website.UserLeague']", 'symmetrical': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'profile'", 'primary_key': 'True', 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['website']
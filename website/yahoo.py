import os
import yql
from yql.storage import FileTokenStore
from fantasy_football.yahoo_credentials import *
from django.conf import settings
import logging
# from google_glass import send_notifications
#
logger = logging.getLogger('debugger')


TOKEN_FILE = 'yahoo_tokens.pkl'
GAME_KEY = 314
LEAGUE_KEY = '314.l.695258'


class YQL(object):
    def q(self, query, kwargs={}):
        y3 = yql.ThreeLegged(YAHOO_CONSUMER_KEY, YAHOO_CONSUMER_SECRET)
        token = self.get_token()
        if kwargs:
            return y3.execute(query, kwargs, token=token)
        else:
            return y3.execute(query, token=token)

    def get_token(self):
        path = settings.YAHOO_CACHE_PATH
        # print path
        token_store = FileTokenStore(path, secret=YAHOO_STORAGE_SECRET)
        stored_token = token_store.get('josh')
        y3 = yql.ThreeLegged(YAHOO_CONSUMER_KEY, YAHOO_CONSUMER_SECRET)
        if stored_token is None:
            query = 'select * from social.connections where owner_guid=me'
            request_token, auth_url = y3.get_token_and_auth_url()
            print "Go to {0}".format(auth_url)
            verifier = raw_input("Please put in token that Yahoo gives you")
            access_token = y3.get_access_token(request_token, verifier)
            token_store.set('josh', access_token)
            return access_token
        else:
            token = y3.check_token(stored_token)
            if token != stored_token:
                token_store.set('josh', token)
            return token

    def player_stats(self, league_key, player_key):
        return self.q("select * from fantasysports.players.stats where league_key=@league_key and player_key=@player_key", {'league_key': league_key, 'player_key': player_key})

    def mass_player_stats(self, league_key, players):
        """
        Players should be a list of player keys
        """
        player_string = ""
        for player in players:
            if len(player_string) != 0:
                player_string += ','
            player_string += "'{0}'".format(player)
        print player_string
        query = "select * from fantasysports.players.stats where league_key=@league_key and player_key in ({0})".format(player_string)
        print query
        return self.q(query, {'league_key':league_key})

    def all_players(self, game_key, start=None, count=None):
        query = "select * from fantasysports.players where game_key=@game_key "
        kwargs = {'game_key': game_key}
        if start:
            kwargs['start'] = start
            query += " and start=@start"
        if count:
            kwargs['count'] = count
            query += " and count=@count"
        print "query", query, kwargs
        return self.q(query, kwargs)

    def player(self, game_key, player_key):
        query = "select * from fantasysports.players where game_key=@game_key and player_key=@player_key"
        kwargs = {'game_key', game_key, 'player_key', player_key}
        return self.q(query, kwargs)
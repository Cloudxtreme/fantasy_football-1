import datetime
import json
import logging
import urllib2
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import utc
import lxml
from oauth2client.client import OAuth2Credentials
from django.core.validators import URLValidator
from django.contrib import admin
from yahoo import YQL
from glass.mirror import Mirror, Timeline
from django.db import connection, IntegrityError
from django.forms.models import model_to_dict
import time

TOKEN_FILE = 'yahoo_tokens.pkl'
GAME_KEY = 314
LEAGUE_KEY = '314.l.695258'


logger = logging.getLogger('website')


"""
Models:
Weekly Stats = Stats for a single week.
Player = NFL Player
League = A collection of players linked to one Google Credential
GoogleCredential = One to many with League. Represents a single person.


Flows:
User login, get Google credentials. Register glass app.
    Create GoogleCredential.
Register league: Scrape league, or manual input. Players are found in the database and linked to the user.
    Create League. Add Players to League.
    /league/ POST
    /league/<league_id>/player/ POST
Pre-gameday: user gets notifications about injured players, etc. Update league every couple hours.
    Cron: Get updates on all active players, get ESPN news on players.
Gameday: user is watching the game, gets notifications.
    Get list of all players in a league. Prioritize them.
    Cron: Update player numbers, check if notification worthy, send notifications, update website.
    /league/<league_id>/ GET

"""



class Player(models.Model):
    # full name, not necessarily ascii
    name = models.CharField(max_length=255)
    player_id = models.IntegerField(unique=True)
    player_key = models.CharField(max_length=32, primary_key=True)
    position_type = models.CharField(max_length=32)
    uniform_number = models.IntegerField(blank=True, null=True)
    image_url = models.TextField(validators=[URLValidator()])
    headshot_url = models.TextField(validators=[URLValidator()])
    is_undroppable = models.IntegerField()
    display_position = models.CharField(max_length=32)
    editorial_player_key = models.CharField(max_length=32)
    editorial_team_full_name = models.CharField(max_length=64)
    editorial_team_key = models.CharField(max_length=32)
    # Comma separated list
    eligible_positions = models.CharField(max_length=255)
    bye_week = models.IntegerField()
    # Used to decide which Players should be updated next.
    last_updated = models.DateTimeField(auto_now=True)
    # Increment this each time a stat is updated, so we can better order objects.
    times_updates = models.IntegerField(default=0)
    status = models.CharField(max_length=16, blank=True, null=True)
    espn_id = models.IntegerField(blank=True, null=True, default=None)

    @classmethod
    def from_json(cls, json):
        player = Player()
        print "JSON", json
        # Load up the straight name to name matches
        for key in ['is_undroppable', 'display_position', 'editorial_player_key', 'editorial_team_abbr',
                    'editorial_team_full_name', 'editorial_team_key', 'image_url', 'player_id', 'player_key',
                    'uniform_number', 'status']:
            # print "setting", key, json[key]
            setattr(player, key, json[key])
        player.bye_week = json['bye_weeks']['week']
        # Make a comma separated list of eligible positions
        # ep = ""
        # for pos in json['eligible_positions'].values():
        #     if len(ep) != 0:
        #         ep += ','
        #     ep += pos
        print "eligible positions", json['eligible_positions'].values()
        pos = json['eligible_positions'].values()
        if isinstance(pos, str):
            player.eligible_positions = pos
        else:
            player.eligible_positions = ",".join(json['eligible_positions'].values()[0])
        player.name = json['name']['full']
        player.headshot_url = json['headshot']['url']
        player.position_type = json['position_type']
        player.save()
        return player

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

class PlayerStat(models.Model):
    week = models.IntegerField(default=0)
    season = models.IntegerField(default=2013)
    player = models.ForeignKey(Player, related_name="stats")
    stat_id = models.IntegerField()
    value = models.IntegerField()

    def update_value(self, value):
        """
        Given the new value, check if we should shoot out a notification.
        """
        if value < self.value:
            logger.warning("Somehow value went down: player: {0}, stat_id: {1}, old_val: {2}, new_val: {3}".format(
                self.player, self.stat_id, self.value, value))
            self.value = value
            self.save()
            return 0
        elif value > self.value:
            diff = float(value) - float(self.value)
            if diff >= stat_notification_minimums[self.stat_id] > 0:
                # Difference meets the requirements. Return True and send out notification.
                self.value = value
                self.save()
                return diff
        return 0

    @classmethod
    def from_json(cls, json, player_key):
        ps = PlayerStat()
        ps.player_id = player_key
        ps.stat_id = json['stat_id']
        ps.value = json['value']
        ps.save()
        return ps

    class Meta:
        unique_together = (('week', 'season', 'player', 'stat_id'))

    def __str__(self):
        return "{0}w{1}: {2} - {3}:{4}".format(self.season, self.week, self.player, stat_id_map[int(self.stat_id)], self.value)

    def __repr__(self):
        return self.__str__()

class GoogleCredential(models.Model):
    """
    Google's provided model was cool, except South didn't like it. This is basically the user account.
    """
    token_expiry = models.DateTimeField(default=datetime.datetime.now())
    access_token = models.CharField(max_length=255)
    token_uri = models.URLField(
        default="https://accounts.google.com/o/oauth2/token")
    invalid = models.BooleanField(default=False)
    token_type = models.CharField(max_length=32)
    expires_in = models.IntegerField()
    client_id = models.CharField(max_length=255)
    # id_token = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=64)
    revoke_uri = models.URLField()
    user_agent = models.CharField(
        max_length=255, blank=True, null=True, default=None)
    user = models.ForeignKey(User, primary_key=True, related_name="google_credential")
    refresh_token = models.CharField(
        max_length=255, blank=True, null=True, default=None)

    @classmethod
    def from_json(cls, json_data, user=None):
        """
        Given a normal credential JSON response from Google, fill in the blanks.
        @param cls:
        @type cls:
        @param json_data:
        @type json_data:
        @param user:
        @type user:
        @return: credential
        @rtype: GoogleCredential
        """
        cred_data = json.loads(json_data)
        print cred_data
        credential = GoogleCredential()
        # DEBUG CODE ONLY
        # if user is None:
        credential.user = user
        for k, v in cred_data['token_response'].items():
            setattr(credential, k, v)
        del cred_data['token_response']
        for k, v in cred_data.items():
            setattr(credential, k, v)
        credential.save()
        return credential

    def needs_refresh(self):
        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        logger.debug("token expiry {0} now {1} needs refresh? {2}".format(
            self.token_expiry, now, self.token_expiry < now))
        return self.token_expiry < now

    def refresh(self, http, force=False):
        # Refreshes if necessary.
        if self.needs_refresh() or force:
            credentials = self.oauth2credentials()
            credentials.refresh(http)
            logger.debug("refresh token {0}".format(credentials.refresh_token))
            logger.debug("token expiry {0} old {1}".format(
                credentials.token_expiry, self.token_expiry))
            self.refresh_token = credentials.refresh_token
            self.token_expiry = credentials.token_expiry
            self.save()
        else:
            logger.debug("Token refresh not needed")

    def oauth2credentials(self):
        kwargs = {
            "token_expiry": self.token_expiry,
            "access_token": self.access_token,
            "token_uri": self.token_uri,
            # "invalid": self.invalid,
            # "token_type": self.token_type,
            # "expires_in": self.expires_in,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "revoke_uri": self.revoke_uri,
            "user_agent": self.user_agent,
            "refresh_token": self.refresh_token,
        }
        return OAuth2Credentials(**kwargs)

    def __str__(self):
        return self.user.username

    def __repr__(self):
        return self.__str__()

class LeaguePlayer(models.Model):
    league = models.ForeignKey('League')
    player = models.ForeignKey('Player')
    order = models.IntegerField()
    fantasy_points = models.FloatField(default=0)
    average_points = models.FloatField(default=0)
    last = models.FloatField(default=0)
    percent_own = models.FloatField(default=0)
    percent_starting = models.FloatField(default=0)
    percent_change = models.FloatField(default=0)
    bench = models.BooleanField(default=False)

    def __str__(self):
        return "{0}: {1}".format(self.league.name, self.player.name)

    def __repr__(self):
        return self.__str__()

    class Meta:
        unique_together = (('league', 'player'))

    @classmethod
    def from_json(cls, league, player):
        player_data = player.league_player_data
        lp = LeaguePlayer(league=league, player=player)
        for attr in ['order', 'fantasy_points', 'average_points', 'last', 'percent_own', 'percent_starting',
                     'percent_change', 'bench']:
            if player_data[attr] == '--':
                player_data[attr] = 0
            setattr(lp, attr, player_data[attr])
        lp.save()
        return lp


LEAGUE_TYPE_CHOICES = (('Yahoo', 'Yahoo'), ('ESPN', 'ESPN'))

class League(models.Model):
    name = models.CharField(max_length=64, default="League")
    players = models.ManyToManyField(Player, through=LeaguePlayer)
    url = models.URLField(unique=True)
    league_type = models.CharField(choices=LEAGUE_TYPE_CHOICES, max_length=32, default="ESPN")
    record = models.CharField(max_length=32, default="0 - 0")
    player_order = models.TextField(blank=True, null=True)

    def scrape(self):
        if self.league_type == 'ESPN':
            scraper = ESPNScraper(self.url)
        elif self.league_type == 'Yahoo':
            scraper = YahooScraper(self.url, credentials=None)
        else:
            return None
        return scraper.scrape()

    def update_league(self):
        data = self.scrape()
        self.name = data['team_name']
        self.record = data['record']
        self.save()
        print "name", self.name
        # Build order list. Compare this to the existing self.player_order. Avoids having to peek at each LP.
        order = ""
        players = []
        player_keys = []
        # Build player list, and check order.
        print data
        order_list = [""] * len(data['players'])
        for player_name, player_data in data['players'].items():
            team_abbr = player_data['team']
            team = team_abbreviations.get(team_abbr.upper(), None)
            position = player_data['position']
            order = player_data['order']

            if order >= len(order_list):
                raise ValueError("Got invalid ordering outside bounds: {0} for player {1}. Order list length: {2}".format(order, player_name, len(order_list)))
            try:
                player = Player.objects.filter(name=player_name).filter(editorial_team_full_name=team).get(display_position=position)
            except Player.DoesNotExist:
                logger.warning("Could not find player {0}, {1}, {2} from url {3}".format(player_name, team, position, self.url))
                continue
            except Player.MultipleObjectsReturned:
                logger.warning("Found multiple players for same player: {0} url: {1}".format(player_name, self.url))
            player.league_player_data = player_data
            players.append(player)
            player_keys.append(player.player_key)
            # Build the order list
            order_list[order] = player_name
        order_string = ",".join(order_list)
        if self.player_order != order_string:
            out_of_order = True
            self.player_order = order_string
            self.save()
        else:
            out_of_order = False
        # Build a list of already associated players. Compare to find deleted and not created.
        league_players = LeaguePlayer.objects.filter(league=self).filter(player__in=player_keys)
        league_player_keys = league_players.values_list('player', flat=True)

        # Use sets to find players not in the league, and league players not in the update.
        lps = set(league_player_keys)
        pls = set(player_keys)
        deleted_player_keys = lps - pls
        added_players = pls - lps

        # Delete the players not in this league.
        LeaguePlayer.objects.filter(league=self).filter(player__in=deleted_player_keys).delete()

        # If this is a re-ordering, we need to touch every player. Touch them before we start adding, but after deleting
        if out_of_order:
            existing_players = LeaguePlayer.objects.prefetch_related('player').filter(league=self)
            for existing_player in existing_players:
                existing_player.order = order_list.index(existing_player.player.name)
                existing_player.save()

        # Add the new players
        for player_key in added_players:
            # Find the player in our list
            player = None
            for p in players:
                if p.player_key == player_key:
                    player = p
            if player is None:
                logger.error("Player key not in players? Really odd. key: {0}".format(player_key))
            order = order_list.index(player.name)
            lp = LeaguePlayer.from_json(league=self, player=player)
            try:
                lp.save()
            except IntegrityError:
                logger.exception("Couldn't save player {0} to league {1}".format(player.name, self.name))
                continue

    def to_json(self):
        data = {
            'name': self.name,
            'record': self.record,
            'url': self.url,
            'league_type': self.league_type,
            'id': self.id
        }

        league_players = LeaguePlayer.objects.prefetch_related().filter(league=self)
        data['players'] = {}
        for league_player in league_players:
            player = league_player.player

            data['players'][player.player_key] = model_to_dict(player)
            data['players'][player.player_key]['id'] = player.player_key
            abbrv = '?'
            for abbreviation, full_name in team_abbreviations.items():
                if full_name == player.editorial_team_full_name:
                    abbrv = abbreviation
            print "abbrv", abbrv
            data['players'][player.player_key]['team_abbr'] = abbrv
            data['players'][player.player_key]['icon'] = team_icons.get(abbrv, None)
            data['players'][player.player_key]['stats'] = {}
            for stat in player.stats.all():
                data['players'][player.player_key]['stats'][stat.stat_id] = model_to_dict(stat)
                data['players'][player.player_key]['stats'][stat.stat_id]['id'] = stat.id
            print data['players'][player.player_key]
        print data
        return data


    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()


class UserLeague(models.Model):
    league = models.ForeignKey('League')
    user_profile = models.ForeignKey('UserProfile')

    def __str__(self):
        return "{0}: {1}".format(self.user_profile.user.username, self.league.name,)

    def __repr__(self):
        return self.__str__()

    class Meta:
        unique_together = (('league', 'user_profile'))


class UserProfile(models.Model):
    user = models.ForeignKey(User, primary_key=True, related_name="profile")
    leagues = models.ManyToManyField(League, through=UserLeague)

    def __str__(self):
        return self.user.username

    def __repr__(self):
        return self.__str__()


class PlayerNews(models.Model):
    player = models.ForeignKey(Player, related_name="news")
    title = models.TextField()
    description = models.TextField()
    published = models.DateTimeField()
    link = models.URLField()
    mobile_link = models.URLField(blank=True, null=True, default=None)
    news_id = models.IntegerField()

    @classmethod
    def from_json(cls, player, json_data):
        news = PlayerNews()
        news.player = player
        news.title = json_data['title']
        news.description = json_data['description']
        news.published = json_data['published']
        news.link = json_data['links']['web']['href']
        news.mobile_link = json_data['links']['mobile']['href']
        news.news_id = json_data['id']
        news.save()
        return news

    class Meta:
        unique_together = (('player', 'news_id'))

    def __str__(self):
        return "({0}) {1}: {2}".format(self.published, self.player.name, self.title)

    def __repr__(self):
        return self.__str__()

class ESPNScraper(object):
    def __init__(self, url):
        self.url = url

    def scrape(self):
        print "Scraping ", self.url
        html = lxml.html.parse(self.url)
        data = {'players': {}}

        team_name = html.xpath('//*[@id="content"]/div[1]/div[4]/div/div/div[3]/div[1]/div[2]/div[1]/h3/text()')
        record = html.xpath('//*[@id="content"]/div[1]/div[4]/div/div/div[3]/div[1]/div[2]/div[2]/h4/text()')
        data['team_name'] = team_name[0].strip()
        data['record'] = record[0].strip()
        # Might break PEPs, but certain rows are going to be ignored. This is easy.
        counter = 0
        all_rows = html.xpath('//*[@id="playertable_0"]/tr')
        for row in all_rows:
            row_list = row.xpath('.//text()')
            print row_list, len(row_list)
            if row_list[0] not in ['STARTERS', 'SLOT', 'BENCH']:
                # Normal example:
                # ['QB', 'Tom Brady', u', NE\xa0QB', '@Buf', 'Sun 1:00', '2', '387.3', '24.2', '--', '--', '26th', '94.3', '100.0', '+0']
                # HC/Defense example
                # ['Bench', 'Seahawks D/ST', u'\xa0D/ST', '@Car', 'Sun 1:00', '3', '221.6', '13.9', '--', '--', '11th', '98.7', '100.0', '+0']
                # ['HC', 'Packers Coach', u'\xa0HC', '@SF', 'Sun 4:25', '7', '61.3', '3.8', '--', '--', '--', '99.3', '100.0', '+0']
                if len(row_list) == 15:
                    status = row_list[3]
                    # Cut status out for uniform rows
                    row_list = row_list[:3] + row_list[4:]
                else:
                    status = 'H'
                player_name = row_list[1]
                player_values = {
                    'current_pos': row_list[0],
                    'name': player_name,
                    'rank': row_list[5],
                    'fantasy_points': row_list[6],
                    'average_points': row_list[7],
                    'percent_starting': row_list[11],
                    'percent_own': row_list[12],
                    'order': counter,
                    'status': status,
                }
                if row_list[8].strip() == '--':
                    player_values['last'] = '0'
                else:
                    player_values['last'] = row_list[8]
                if row_list[9].strip() == '--':
                    player_values['projected_points'] = '0'
                else:
                    player_values['projected_points'] = row_list[8]
                print 'change', player_name, row_list[13], len(row_list)
                if row_list[13].strip()[0] == '+':
                    player_values['percent_change'] = row_list[13].strip()[1:]
                else:
                    player_values['percent_change'] = str(0 - float(row_list[13].strip()[1:]))
                if row_list[0] == "Bench":
                    player_values['bench'] = True
                else:
                    player_values['bench'] = False
                abbr_pos = row_list[2].encode('ascii', 'replace').replace('?', ' ').strip().replace(', ', '').split()[0]
                if abbr_pos == 'HC':

                    player_values['position'] = 'HC'
                    player_values['team'] = row_list[1].split()[0]
                elif abbr_pos == 'D/ST':
                    player_values['position'] = 'D/ST'
                    player_values['team'] = row_list[1].split()[0]
                else:
                    player_values['position'] = row_list[2].encode('ascii', 'replace').replace('?', ' ').strip().replace(', ', '').split()[1]
                    player_values['team'] = abbr_pos
                print player_values
                # Only increment on player rows.
                counter += 1
                data['players'][player_name] = player_values

        print data
        return data

class YahooScraper(object):
    def __init__(self, url, credentials):
        self.url = url
        self.credentials = credentials

    def scrape(self):
        pass


class ESPNNewsScraper(object):
    def __init__(self, api_key):
        self.api_key = api_key

    def get_all_players(self):
        offset = 0
        results = 100000
        # ID: fullName

        # Loop until break
        while (offset + 1) * 50 < results:
            resolve_list = {}
            player_dict = {}
            url = self.player_id_url(offset=offset * 50)
            url_data = self.fetch_json(url)
            results = url_data['resultsCount']
            players = url_data['sports'][0]['leagues'][0]['athletes']
            for player in players:
                player_dict[player['id']] = player['fullName']
            player_instances = Player.objects.filter(name__in=player_dict.values())
            for player_id, player_name in player_dict.items():
                try:
                    player_instance = player_instances.get(name=player_name)
                    player_instance.espn_id = player_id
                    # logger.info("Saving ESPN id {0} to player {1}.".format(player_id, player_name))
                    player_instance.save()
                except Player.DoesNotExist:
                    # Linemen, individual D players, etc.
                    # logger.warning("ESPN has a player we don't: {0}, id: {1}".format(player_name, player_id))
                    continue
                except Player.MultipleObjectsReturned:
                    logger.error("Player name collision because ESPN didn't provide team/position. Adding {0}, "
                                   "id: {1} to resolve list.".format(player_name, player_id))
                    resolve_list[player_id] = player_name
            # Resolve our collisions
            self.resolve_conflicts(resolve_list)
            # print url_data
            # print player_dict
            time.sleep(0.5)
            offset += 1
            # break

    def get_player_news(self, player_id):
        url = self.player_news_url(player_id=player_id)
        json_data = self.fetch_json(url)
        return json_data['headlines']

    def resolve_conflicts(self, resolve_list):
        pass

    def player_id_url(self, offset=0):
        return "http://api.espn.com/v1/sports/football/nfl/athletes?apikey={0}&offset={1}".format(self.api_key, offset)

    def fetch_json(self, url):
        url_data = json.loads(urllib2.urlopen(url).read())
        if url_data['status'] != 'success':
            raise ValueError("Failed status: {0}".format(url_data['status']))
        return url_data

    def player_news_url(self, player_id, offset=0):
        url = "http://api.espn.com/v1/sports/football/nfl/news/?athletes={0}&insider=no&apikey={1}&offset={2}".format(
            player_id, self.api_key, offset)
        return url

    def ticker_url(self, offset=0):
        url = "http://api.espn.com/v1/sports/football/nfl/news/?insider=no&apikey={0}&offset={1}&limit=50".format(
            self.api_key, offset)
        return url

    def seed_player_news(self):
        for player in Player.objects.all():
            if player.espn_id:
                news = self.get_player_news(player.espn_id)
                for news_item in news:
                    try:
                        player_news = PlayerNews.from_json(player, news_item)
                        logger.info("Found news for player {0}, headline: {1}".format(player.name, player_news.title))
                    except Exception:
                        logger.exception()
                        continue

    def filter_all_news(self):
        """
        Grabs all the headlines, sees if they apply to any of our players, if so, attempts to create a story about
        them.
        Should be run at least once a minute.
        """
        url = self.ticker_url()
        json_data = self.fetch_json(url)
        for headline in json_data['headlines']:
            # Make a list of espn_ids to search the DB for.
            espn_ids = []
            for category in headline['categories']:
                if category['type'] == "athlete":
                    espn_ids.append(category["athleteId"])
            if len(espn_ids) == 0:
                continue
            # Get all affected players
            players = Player.objects.filter(espn_id__in=espn_ids)
            if len(players) == 0:
                continue
            for player in players:
                try:
                    player_news = PlayerNews.from_json(player, headline)
                except Exception:
                    continue
                logger.info("Matched news to player {0}, headline: {1}".format(player.name, player_news.title))


class UpdateManager(object):
    """
    Decides which players need to be updated, gets the updates as a batch from Yahoo, then sends them over to the
    PlayerStats objects, figures out which changed, and which need to be updated.
    """
    # TODO make this smarter and only check the players currently playing.
    def get_next_players(self):
        """
        Find all players connected to a league. The rest don't really matter right now. Update them, then see if
        anyone needs notifications.
        """
        # Find player who has the longest since updated time.
        player = Player.objects.all().order_by('last_updated')[0]
        print player.last_updated
        self.get_player_stats(player.player_key)

    def get_player_stats(self, player_key):
        yql = YQL()
        stats = yql.player_stats(LEAGUE_KEY, player_key)
        # Check if we have a stats object already existing in the DB. If not, create.
        try:
            stat_db = PlayerStat.objects.get(player=player_key)
        except PlayerStat.DoesNotExist:
            stat_db = PlayerStat.from_json(stats, player_key)
        player_key = stats.rows[0]['player_key']
        self.update_player_stats(stats.rows[0]['player_stats']['stats']['stat'], player_key)


    def load_all_players(self, start=1):
        yql = YQL()
        players = yql.all_players(GAME_KEY, start=start, count=25)
        while players.rows != []:
            for player in players.rows:
                p = Player.from_json(player)
                print p
            start = start + 25
            players = yql.all_players(GAME_KEY, start=start, count=25)

    def load_all_player_stats(self, start=0, count=25):
        yql = YQL()
        # Get existing player stats
        ps = PlayerStat.objects.all().values_list('player_id', flat=True)
        print "exclude list", ps
        players = Player.objects.exclude(player_key__in=ps)
        while start+count < len(players):
            update_players = Player.objects.values_list('player_key', flat=True)[start:start+count]
            update_stats = yql.mass_player_stats(LEAGUE_KEY, update_players)
            for update_stat in update_stats.rows:
                print "stats", update_stat
                try:
                    stats = update_stat['player_stats']['stats']['stat']
                except Exception:
                    continue
                player_key = update_stat['player_key']
                for stat in stats:
                    try:
                        ps = PlayerStat.from_json(stat, player_key=player_key)
                    except Exception:
                        continue
                    print ps
            start = start+count


    def update_player_stats(self, stats, player_key):
        """
        After fetching a player's stats via YQL, update the DB object and possibly send a notification.
        stats is of the form [{'stat_id': '4', 'value': '0'}, {'stat_id'...]
        """
        for stat in stats:
            # print "stat", stat
            try:
                # TODO check if this is prefetching too much.
                ps = PlayerStat.objects.prefetch_related('player').filter(player_id=player_key).get(stat_id=stat['stat_id'])
                difference = ps.update_value(stat['value'])
                logger.debug("Got {0} difference for player: {1} on stat: {2}".format(difference, player_key, stat['stat_id']))
                if difference > 0:
                    self.send_notifications(ps, difference, player_key)
            except PlayerStat.DoesNotExist:
                self.add_player(player_key)
            except PlayerStat.MultipleObjectsReturned:
                logger.exception("Got multiple player stats for the same player_key/stat_id combination.")

    def add_player(self, player_key):
        yql = YQL()
        p = yql.player(GAME_KEY, player_key)
        player = Player.from_json(p)
        logger.debug("Added new player: {0}".format(player.name))

    def send_notifications(self, ps, difference, player_key):
        """
        Given a player who has new stats (which are above the thresholds set), send out notifications to all users
        that have that player.
        """
        player = Player.objects.get(player_key=player_key)
        league_players = LeaguePlayer.objects.prefetch_related('league').filter(player_id=player_key)
        # print "league_players", league_players, league_players.query
        user_leagues = UserLeague.objects.prefetch_related('user_profile__user').filter(league_id__in=league_players)
        # print user_leagues,  user_leagues.query
        user_profiles = user_leagues.values_list('user_profile', flat=True)
        # print "profiles", user_profiles, user_profiles.query
        users = User.objects.prefetch_related('google_credential').filter(profile__in=user_profiles)
        # print "users", users, users.query
        # for q in connection.queries:
        #     print q
        for user in users:
            gn = GlassNotification(user, ps, difference, player)
            gn.send()

class GlassNotification(object):
    def __init__(self, user, ps, difference, player):
        self.user = user
        self.ps = ps
        self.difference = difference
        self.player = player
        self.cred = user.google_credential
        self.mirror = Mirror.from_credentials(self.cred.all()[0].oauth2credentials())

    def send(self):
        print "Sending notification for ", self.user, self.ps, self.difference, self.player
        html = """
<article>
<figure>
<img src="{headshot}" width="185" height="241" >
</figure>

<figure>
<img src="{team_icon}"
width="185" height="119" style="margin-top:241px">
</figure>

<section >
<h4 style="font-size:50px; font-weight:bold">{player_name}</h4>
<p style="color:red; font-weight:bold">{stat_notification}</p>
<p style="font-size:30px;">{stat1}</p>
<p style="font-size:30px;">{stat2}</p>
<p style="font-size:30px;">{stat3}</p>
</section>
</article>
"""
        team_abbr = team_abbreviations[self.player.editorial_team_full_name],
        kwargs = {
            'player_name': self.player.name,
            'score': "{0} {1}".format(self.difference, stat_id_map[self.ps.stat_id]),
            'team': team_abbr,
            'team_icon': team_icons[team_abbr]
        }
        html = html.format(**kwargs)
        print html
        timeline = Timeline(html=html)
        # timeline = Timeline(text="{0} {1}".format(self.player.name,  "{0} {1}".format(self.difference, stat_id_map[self.ps.stat_id])))
        timeline.notify = True
        print self.mirror.post_timeline(timeline)
        print self.mirror.list_timeline()
        print "sent"


# Map the stat ids to the name of the stat model fields.
stat_id_map = {
    4: 'Pass Yds',
    5: 'Pass TD',
    6: 'Int',
    9: 'Rush Yds',
    10: 'Rush TD',
    12: 'Rec Yds',
    13: 'Rec TD',
    15: 'Ret TD',
    16: '2-PT',
    18: 'Fum Lost',
    57: 'Fum Ret TD',
    19: 'FG 0-19',
    20: 'FG 20-29',
    21: 'FG 30-39',
    22: 'FG 40-49',
    23: 'FG 50+',
    29: 'PAT Made',
    31: 'Pts Allow',
    32: 'Sack',
    33: 'Int',
    34: 'Fum Rec',
    35: 'TD',
    36: 'Safe',
    37: 'Blk Kick',
    49: 'Kick and Punt Ret TD',
    50: 'Pts Allow 0',
    51: 'Pts Allow 1-6',
    52: 'Pts Allow 7-13',
    53: 'Pts Allow 14-20',
    54: 'Pts Allow 21-27',
    55: 'Pts Allow 28-34',
    56: 'Pts Allow 35+',
}

stat_notification_minimums = {
    4: 0,#'Pass Yds',
    5: 1,#'Pass TD',
    6: 1,#'Int',
    9: 0,#'Rush Yds',
    10: 1,#'Rush TD',
    12: 0,#'Rec Yds',
    13: 1,#'Rec TD',
    15: 1,#'Ret TD',
    16: 1,#'2-PT',
    18: 1,#'Fum Lost',
    57: 1,#'Fum Ret TD',
    19: 1,#'FG 0-19',
    20: 1,#'FG 20-29',
    21: 1,#'FG 30-39',
    22: 1,#'FG 40-49',
    23: 1,#'FG 50+',
    29: 1,#'PAT Made',
    31: 1,#'Pts Allow',
    32: 0,#'Sack',
    33: 1,#'Int',
    34: 1,#'Fum Rec',
    35: 1,#'TD',
    36: 1,#'Safe',
    37: 1,#'Blk Kick',
    49: 1,#'Kick and Punt Ret TD',
    50: 0,#'Pts Allow 0',
    51: 0,#'Pts Allow 1-6',
    52: 0,#'Pts Allow 7-13',
    53: 0,#'Pts Allow 14-20',
    54: 0,#'Pts Allow 21-27',
    55: 0,#'Pts Allow 28-34',
    56: 0,#'Pts Allow 35+',
}

team_abbreviations = {
"ARI": "Arizona Cardinals",
"ATL": "Atlanta Falcons",
"BAL": "Baltimore Ravens",
"BUF": "Buffalo Bills",
"CAR": "Carolina Panthers",
"CHI": "Chicago Bears",
"CIN": "Cincinnati Bengals",
"CLE": "Cleveland Browns",
"DAL": "Dallas Cowboys",
"DEN": "Denver Broncos",
"DET": "Detroit Lions",
"GB": "Green Bay Packers",
"HOU": "Houston Texans",
"IND": "Indianapolis Colts",
"JAX": "Jacksonville Jaguars",
"KC": "Kansas City Chiefs",
"MIA": "Miami Dolphins",
"MIN": "Minnesota Vikings",
"NE": "New England Patriots",
"NO": "New Orleans Saints",
"NYG": "New York Giants",
"NYJ": "New York Jets",
"OAK": "Oakland Raiders",
"PHI": "Philadelphia Eagles",
"PIT": "Pittsburgh Steelers",
"SD": "San Diego Chargers",
"SEA": "Seattle Seahawks",
"SF": "San Francisco 49ers",
"STL": "Saint Louis Rams",
"TB": "Tampa Bay Buccaneers",
"TEN": "Tennessee Titans",
"WAS": "Washington Redskins",
"WSH": "Washington Redskins",
}

team_to_editorial_team_full_name = {
'Falcons': 'Atlanta Falcons',
'Bills': 'Buffalo Bills',
'Bears': 'Chicago Bears',
'Bengals': 'Cincinnati Bengals',
'Browns': 'Cleveland Browns',
'Cowboys': 'Dallas Cowboys',
'Broncos': 'Denver Broncos',
'Lions': 'Detroit Lions',
'Packers': 'Green Bay Packers',
'Titans': 'Tennessee Titans',
'Colts': 'Indianapolis Colts',
'Chiefs': 'Kansas City Chiefs',
'Raiders': 'Oakland Raiders',
'Rams': 'St. Louis Rams',
'Dolphins': 'Miami Dolphins',
'Vikings': 'Minnesota Vikings',
'Patriots': 'New England Patriots',
'Saints': 'New Orleans Saints',
'Giants': 'New York Giants',
'Jets': 'New York Jets',
'Eagles': 'Philadelphia Eagles',
'Cardinals': 'Arizona Cardinals',
'Steelers': 'Pittsburgh Steelers',
'Chargers': 'San Diego Chargers',
'49ers': 'San Francisco 49ers',
'Seahawks': 'Seattle Seahawks',
'Buccaneers': 'Tampa Bay Buccaneers',
'Redskins': 'Washington Redskins',
'Panthers': 'Carolina Panthers',
'Jaguars': 'Jacksonville Jaguars',
'Ravens': 'Baltimore Ravens',
'Texans': 'Houston Texans',
}

team_icons = {
"ARI": "cardinals.gif",
"ATL": "falcons.gif",
"BAL": "ravens.gif",
"BUF": "bills.gif",
"CAR": "panthers.gif",
"CHI": "bears.gif",
"CIN": "bengals.gif",
"CLE": "browns.gif",
"DAL": "cowboys.gif",
"DEN": "broncos.gif",
"DET": "lions.gif",
"GB": "packers.gif",
"HOU": "texans.gif",
"IND": "colts.gif",
"JAX": "jaguars.gif",
"KC": "chiefs.gif",
"MIA": "dolphins.gif",
"MIN": "vikings.gif",
"NE": "patriots.gif",
"NO": "saints.gif",
"NYG": "giants.gif",
"NYJ": "jets.gif",
"OAK": "raiders.gif",
"PHI": "eagles.gif",
"PIT": "steelers.gif",
"SD": "chargers.gif",
"SEA": "seahawks.gif",
"SF": "49ers.gif",
"STL": "rams.gif",
"TB": "buccaneers.gif",
"TEN": "titans.gif",
"WAS": "redskins.gif",
}


admin.site.register(GoogleCredential)
admin.site.register(Player)
admin.site.register(PlayerStat)
admin.site.register(UserLeague)
admin.site.register(UserProfile)
admin.site.register(LeaguePlayer)
admin.site.register(League)
admin.site.register(PlayerNews)


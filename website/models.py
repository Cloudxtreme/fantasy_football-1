import datetime
import json
import logging
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import utc
from oauth2client.client import OAuth2Credentials
from django.core.validators import URLValidator
from django.contrib import admin
from yahoo import YQL
from glass.mirror import Mirror, Timeline
from scrapers import ESPNScraper, YahooScraper
# from google_glass import send_notifications
from django.db import connection, IntegrityError

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

    @classmethod
    def from_json(cls, json):
        player = Player()
        print "JSON", json
        # Load up the straight name to name matches
        for key in ['is_undroppable', 'display_position', 'editorial_player_key', 'editorial_team_abbr', 'editorial_team_full_name', 'editorial_team_key', 'image_url', 'player_id', 'player_key', 'uniform_number']:
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
            logger.warning("Somehow value went down: player: {0}, stat_id: {1}, old_val: {2}, new_val: {3}".format(self.player, self.stat_id, self.value, value))
            self.value = value
            self.save()
            return 0
        elif value > self.value:
            diff = float(value) - float(self.value)
            if diff >= stat_notification_minimums[self.stat_id] and stat_notification_minimums[self.stat_id] > 0:
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

    def __str__(self):
        return "{0}: {1}".format(self.league.name, self.player.name)

    def __repr__(self):
        return self.__str__()

    class Meta:
        unique_together = (('league', 'player'))

LEAGUE_TYPE_CHOICES = (('Yahoo', 'Yahoo'), ('ESPN', 'ESPN'))

class League(models.Model):
    name = models.CharField(max_length=64, default="League")
    players = models.ManyToManyField(Player, through=LeaguePlayer)
    url = models.URLField(blank=True, null=True)
    league_type = models.CharField(choices=LEAGUE_TYPE_CHOICES, max_length=32, default="ESPN")

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
        for player_name, team_pos in data['players'].items():
            team = team_abbreviations[team_pos['team'].upper()]
            position = team_pos['position']
            try:
                player = Player.objects.filter(name=player_name).filter(editorial_team_full_name=team).get(display_position=position)
                # Create a player-league relationship
                lp = LeaguePlayer(league=self, player=player)
                # Try to add the relationship. Since we have key restraints, this will fail if it already exists to
                # that player.
                try:
                    lp.save()
                except IntegrityError:
                    continue
            except Player.DoesNotExist:
                logger.warning("Could not find player {0} from url {1}".format(player_name, self.url))
                continue
            except Player.MultipleObjectsReturned:
                logger.warning("Found multiple players for same player: {0} url: {1}".format(player_name, self.url))
            # Now look for deleted players.
        existing_players = self.players.all()
        for existing_player in existing_players:
            if existing_player.name not in data['players']:
                # Delete the relationship, player no longer in league.
                relationship = LeaguePlayer.objects.filter(league=self).filter(player=existing_player)
                logger.debug("Deleting dropped player {0} from league {1}".format(existing_player, self.name))
                relationship.delete()

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

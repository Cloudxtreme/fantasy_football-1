import json
import logging
from website.models import UserProfile, League, UserLeague, Player, PlayerStat, stat_id_map, LeaguePlayer, UpdateManager, team_abbreviations, team_to_editorial_team_full_name, team_icons
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotFound, HttpResponse
from django.contrib import messages


logger = logging.getLogger('api')


def scores(request, user_id=None):
    if request.method != 'GET':
        return HttpResponseBadRequest("Only GET supported.")
    if user_id is None:
        user_id = request.user.id
        if user_id is None:
            return HttpResponseBadRequest("User does not exist.")
    user_profile = UserProfile.objects.get(user_id=user_id)
    user_league = UserLeague.objects.prefetch_related('league__players').get(user_profile=user_profile)
    league = user_league.league
    players = league.players.all()
    player_list = league.players.all().values_list('player_key', flat=True)
    stats = PlayerStat.objects.filter(player__in=player_list)
    json_return = {}
    for player in players:
        json_return[player.player_key] = model_to_dict(player)
        json_return[player.player_key]['team_abbr'] = team_abbreviations.get(player.editorial_team_full_name, 'FA')
        json_return[player.player_key]['stats'] = {}
        for stat in stats.filter(player=player):
            json_return[player.player_key]['stats'][stat.stat_id] = {'value': stat.value, 'category': stat_id_map[stat.stat_id]}

    print json_return
    return render_to_json(request, json_return)


def players(request):
    if request.method == "POST":
        player_name = request.POST['player_name'].strip()
        try:
            player = Player.objects.get(name__iexact=player_name)
        except Player.MultipleObjectsReturned:
            # TODO Send the user an error instead of just choosing a player for them when multiple match their search.
            player = Player.objects.filter(name__iexact=player_name)[0]
        except Player.DoesNotExist:
            # TODO Try to find the player on YQL, if we don't just grab all of them first.
            return HttpResponseNotFound("No player found.")
        user_profile = UserProfile.objects.get(user=request.user)
        league = user_profile.leagues.all()[0]
        league_player = LeaguePlayer(league=league, player=player).save()
        stats = PlayerStat.objects.filter(player=player)
        json_return = {}
        json_return[player.player_key] = model_to_dict(player)
        json_return[player.player_key]['stats'] = {}
        for stat in stats.filter(player=player):
            json_return[player.player_key]['stats'][stat.stat_id] = {'value': stat.value, 'category': stat_id_map[stat.stat_id]}
        if request.is_ajax():
            return render_to_json(request, json_return)
        else:
            return HttpResponseRedirect('/')
    else:
        return HttpResponseBadRequest("Only POST supported currently.")

def leagues(request, league_id=None):
    if request.method == "POST":
        if not request.user.is_authenticated():
            return HttpResponseBadRequest("User must be authenticated to add a league.")
        if league_id is not None:
            return HttpResponseBadRequest("League ID not legal argument when adding league.")
        try:
            user_profile = UserProfile.objects.get(user=request.user.id)
        except UserProfile.DoesNotExist:
            return HttpResponseBadRequest("Could nto find User Profile for user id: {0}.".format(request.user.id))
        print request.POST
        league_url = request.POST.get('league_url', None)
        if league_url is None:
            return HttpResponseBadRequest("League URL cannot be none.")
        league_type = request.POST.get('league_type', 'ESPN')
        league = League(url=league_url.strip(), league_type=league_type)
        league.save()
        league.update_league()
        user_league = UserLeague(league=league, user_profile=user_profile)
        user_league.save()
        league_json = league_to_json(league)
        return render_to_json(request, league_json)

    elif request.method == "GET":
        if request.user.is_authenticated():
            user = request.user.id
            user_profile = UserProfile.objects.get(user=user)
        else:
            user = None
        if user is None and league_id is None:
            return HttpResponseBadRequest("Must either be a logged in user or supply a league ID")
        leagues = League.objects.all()
        if user is not None:
            leagues = leagues.filter(userprofile=user)
        if league_id is not None:
            leagues = leagues.filter(id=league_id)
        json_return = {}
        for league in leagues:
            # print "league", league
            json_return[league.id] = league_to_json(league)
        return render_to_json(request, json_return)

def league_to_json(league):
    data = {
        'name': league.name,
        'record': league.record,
        'url': league.url,
        'league_type': league.league_type,
        'id': league.id
    }

    league_players = LeaguePlayer.objects.prefetch_related().filter(league=league)
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


def render_to_json(request, data):
    # msgs = {}
    # messages_list = messages.get_messages(request)
    # count = 0
    # for message in messages_list:
    #     msgs[count] = {'message': message.message, 'level': message.level}
    #     count += 1
    # data['messages'] = msgs
    # if request.user.is_authenticated():
    #     data['profile'] = model_to_dict(get_profile(request.user.id))
    # else:
    #     data['profile'] = {}
    return HttpResponse(
        json.dumps(data, ensure_ascii=False),
        mimetype=request.is_ajax() and "application/json" or "text/html"
    )

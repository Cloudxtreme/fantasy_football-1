import json
import logging
from website.models import UserProfile, League, UserLeague, Player, PlayerStat, stat_id_map, LeaguePlayer, UpdateManager
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

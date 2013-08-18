# # from glass.mirror import Mirror
# # from models import Player, PlayerStat, LeaguePlayer, League, UserLeague
# from website.models import Player
# def send_notifications(player_stat, difference, player_key):
#     # pass
#     # Find the player associated with the stat.
#     league_players = LeaguePlayer.objects.prefetch_related('league').filter(player_id=player_key)
#     user_leagues = UserLeague.objects.prefetch_related('user_profile__user').filter(league_id__in=league_players)
#     print user_leagues
import lxml.html
import re
import logging


logger = logging.getLogger('website')


class ESPNScraper(object):
    def __init__(self, url):
        self.url = url

    def scrape(self):
        html = lxml.html.parse('http://games.espn.go.com/ffl/clubhouse?leagueId=844419&teamId=1&seasonId=2012')
        data = {'players': {}}
        player_names = html.xpath('//*[@class="playertablePlayerName"]/a/text()')
        team_pos = html.xpath('//*[@class="playertablePlayerName"]/text()')
        team_name = html.xpath('//*[@id="content"]/div[1]/div[4]/div/div/div[3]/div[1]/div[2]/div[1]/h3/text()')
        record = html.xpath('//*[@id="content"]/div[1]/div[4]/div/div/div[3]/div[1]/div[2]/div[2]/h4/text()')
        for i in range(1, len(player_names)):
            player = player_names[i]
            try:
                # Assume normal problems
                team_position = team_pos[i].encode('ascii', 'replace').replace('?', ' ')
                nil, team, position = team_position.split()
            except ValueError:
                # Head coach? Defensive player?
                if team_pos[i] == 'D/ST':
                    team = re.search("(\w+)\s+D/ST", team_position).group(1)
                    position = "Defense"
                elif team_pos[i] == 'HC':
                    team = re.search("(\w+)\s+Coach", team_position).group(1)
                    position = "Head Coach"
                else:
                    logger.error("Unknown string for team_pos: {0} from URL {1}".format(team_position.encode('ascii', 'replace'), self.url))
                    continue
            data['players'][player] = {}
            data['players'][player]['team'] = team
            data['players'][player]['position'] = position
            data['team_name'] = team_name[0].strip()
            data['record'] = record[0].strip()
        return data

class YahooScraper(object):
    def __init__(self, url, credentials):
        self.url = url
        self.credentials = credentials

    def scrape(self):
        pass

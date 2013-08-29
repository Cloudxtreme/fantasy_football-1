import lxml.html
import re
import logging
from django.conf import settings

logger = logging.getLogger('website')


class ESPNScraper(object):
    def __init__(self, url):
        self.url = url

    def scrape(self):
        html = lxml.html.parse(self.url)
        data = {'players': {}}
        player_names = html.xpath('//*[@class="playertablePlayerName"]/a/text()')
        team_pos = html.xpath('//*[@class="playertablePlayerName"]/text()')
        team_name = html.xpath('//*[@id="content"]/div[1]/div[4]/div/div/div[3]/div[1]/div[2]/div[1]/h3/text()')
        record = html.xpath('//*[@id="content"]/div[1]/div[4]/div/div/div[3]/div[1]/div[2]/div[2]/h4/text()')
        for i in range(1, len(player_names)):
            player = player_names[i]
            try:
                # Assume normal problems
                team_position = team_pos[i].encode('ascii', 'replace').replace('?', ' ').strip()
                nil, team_abbr, position = team_position.split()
                team = settings.TEAM_ABBREVIATIONS[team_abbr.upper()]
            except ValueError:
                # Head coach? Defensive player?
                print "trying to fill", team_position
                if team_position == 'D/ST':
                    team_short = re.search("(\w+)\s+D/ST", player_names[i]).group(1)
                    team = settings.TEAM_TO_EDITORIAL_TEAM_FULL_NAME[team_short]
                    position = "Defense"
                elif team_position == 'HC':
                    team_short = player_names[i].split()[0]
                    team = settings.TEAM_TO_EDITORIAL_TEAM_FULL_NAME[team_short]
                    position = "Head Coach"
                else:
                    logger.error("Unknown string for team_pos: {0} from URL {1}".format(team_position.encode('ascii', 'replace'), self.url))
                    continue
            data['players'][player] = {}
            data['players'][player]['order'] = i
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

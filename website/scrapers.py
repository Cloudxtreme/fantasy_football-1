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

        team_name = html.xpath('//*[@id="content"]/div[1]/div[4]/div/div/div[3]/div[1]/div[2]/div[1]/h3/text()')
        record = html.xpath('//*[@id="content"]/div[1]/div[4]/div/div/div[3]/div[1]/div[2]/div[2]/h4/text()')
        data['team_name'] = team_name[0].strip()
        data['record'] = record[0].strip()
        # Might break PEPs, but certain rows are going to be ignored. This is easy.
        counter = 0
        all_rows = html.xpath('//*[@id="playertable_0"]/tr')
        for row in all_rows:
            row_list = row.xpath('.//text()')
            print row_list
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

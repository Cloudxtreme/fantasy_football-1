"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from scrapers import ESPNScraper

class ScraperTest(TestCase):
    def test_espn_basic(self):
        url = 'http://games.espn.go.com/ffl/clubhouse?leagueId=844419&teamId=8&seasonId=2013'
        scraper = ESPNScraper(url)
        scraper.scrape()
import json
import urllib2
import time
import lxml.html
import re
import logging
from django.conf import settings
from website.models import Player

logger = logging.getLogger('website')




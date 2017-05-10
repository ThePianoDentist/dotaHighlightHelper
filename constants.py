import configparser
import os
import traceback

from searches.courierkill import CourierkillSearch
from searches.multikill import MultikillSearch
from searches.smoke import SmokeSearch
from searches.teamfight import TeamwipeSearch, TeamfightSearch
from searches.ultimates.blackhole import BlackholeSearch
from searches.ultimates.chrono import ChronoSearch
from searches.ultimates.rp import RpSearch

config = configparser.ConfigParser()
config.read('config.ini')

REPLAY_FOLDER = os.path.normpath(config.get('settings', 'REPLAY_FOLDER'))
PARSER_FOLDER = os.path.normpath(config.get('settings', 'PARSER_FOLDER'))
try:
    MAX_DOWNLOAD_THREADS = min(int(config.get('settings', 'MAX_PARALLEL_DOWNLOADS')), 5)
except configparser.NoOptionError:
    MAX_DOWNLOAD_THREADS = 5

ALLOWABLE_SEARCHES = {"smoketimings": SmokeSearch, "courierkills": CourierkillSearch, "multikills": MultikillSearch,
                      "teamfights": TeamfightSearch, "teamwipes": TeamwipeSearch,
                      #"neutraldenies": NeutraldenySearch,
                      "chronos": ChronoSearch, "blackholes": BlackholeSearch, "rps": RpSearch}

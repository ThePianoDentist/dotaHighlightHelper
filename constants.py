import configparser
import os

config = configparser.ConfigParser()
config.read('config.ini')

REPLAY_FOLDER = os.path.normpath(config.get('settings', 'REPLAY_FOLDER'))
CLARITY_FOLDER = os.path.normpath(config.get('settings', 'CLARITY_FOLDER'))
APIKEY = os.path.normpath(config.get('settings', 'APIKEY'))
MAX_PARALLEL_DOWNLOADS = int(config.get('settings', 'MAX_PARALLEL_DOWNLOADS'))
SEVENZIP_PATH = os.path.normpath(config.get('settings', 'SEVENZIP_PATH'))

ALLOWABLE_SEARCHES = {"smoketimings"}
# Ideas for adding allowable searches
# Teamfight starts
# Mid-lane ganks
# Roaming support laning kills
# Interesting jukes
# skillshot hits?
# big ultis? i.e. 4 man chronos, big black holes etc
# anything really :D

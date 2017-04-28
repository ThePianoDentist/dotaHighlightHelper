import configparser
import os

config = configparser.ConfigParser()
config.read('config.ini')

REPLAY_FOLDER = os.path.normpath(config.get('settings', 'REPLAY_FOLDER'))
CLARITY_FOLDER = os.path.normpath(config.get('settings', 'CLARITY_FOLDER'))

ALLOWABLE_SEARCHES = {"smoketimings", "courierkills", "multikills", "teamfights"}
# Ideas for adding allowable searches
# Teamfight starts
# Mid-lane ganks
# Roaming support laning kills
# Interesting jukes
# skillshot hits?
# big ultis? i.e. 4 man chronos, big black holes etc
# anything really :D

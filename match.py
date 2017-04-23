import codecs
import json
import subprocess

from api_requests import request_
from constants import *


class Match:
    def __init__(self, id):
        self.id = int(id)
        self.our_heroes = []
        self.download_path = REPLAY_FOLDER + os.path.normpath("/%d.dem.bz2") % self.id
        self.already_have_replay = self.check_have_replay()  # TODO maybe wants to be property. so we can tell at any time whether we have replay
        self.is_radiant = None
        self.interesting_ticks = set()
        self.replay_url = self.generate_replay_url()
        # TODO is it worth getting the whole game data from open dota api. might come in useful?

    @property
    def file_path(self):
        return self.download_path.replace(".bz2", "")

    def add_hero(self, hero_id):
        self.our_heroes.append(hero_id)

    def add_side(self, is_radiant):
        self.is_radiant = is_radiant

    def check_have_replay(self):
        return os.path.exists(self.file_path)

    def generate_replay_url(self):
        if self.already_have_replay:
            return None  # Not going to be downloading. so dont need. not worth the api call
        else:
            result = json.loads(str(request_("https://api.opendota.com/api/replays?match_id=%d" % self.id)))[0]
            return "http://replay{0}.valve.net/570/{1}_{2}.dem.bz2".format(
                result["cluster"], result["match_id"], result["replay_salt"]
            )

    def parse_replay(self, search_type):
        jar = os.path.normpath("%s/target/%s.one-jar.jar" % (CLARITY_FOLDER, search_type))
        fp = os.path.normpath("%s/%d.dem" % (REPLAY_FOLDER, self.id))
        p = subprocess.Popen(["java", "-jar", jar, fp], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # TODO do i need to be checking/reporting err?
        return codecs.iterdecode(p.stdout, 'utf8')

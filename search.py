import codecs
import json
import re
import subprocess
import traceback
from concurrent import futures

from api_requests import get_match_details, request_, download_and_extract
from constants import *
from match import Match


class Search(object):

    def __init__(self, team_id, only_download, patch=None, time_range=None, tick_offset=60, odota_file=None):
        """

        :param team_id:
        :param only_download:
        :param patch:
        :param time_range:
        :param tick_offset:
        """
        # TODO what is reasonable timerange
        self.matches_by_id = {}
        self.search_phrase = None
        self.matches = set()
        self.match_ids = None
        self.team_id = team_id
        self.patch = patch
        self.time_range = time_range
        self.only_download = only_download
        self.tick_offset = tick_offset
        self.multiline = False
        self.odota_file = odota_file
        self.hero = None

    def match_from_id(self, match_id):
        """
        :rtype: Match
        """
        return self.matches_by_id[match_id]

    def find_match_ids_odota(self):
        with open(self.odota_file) as f:
            data = json.load(f)
        for match in data["rows"]:
            if match["match_id"] not in self.match_ids:
                self.match_ids.add(match["match_id"])
                self.matches_by_id[match.id] = match
            else:
                match.add_hero(match["hero_id"])

    # def find_match_ids(self):
    #     # Hard to tidy as its just one query param (sql)
    #     url = "https://api.opendota.com/api/explorer?sql=SELECT%0Amatches.match_id%2C%0Amatches.start_time%2C%0A((player_matches.player_slot%20%3C%20128)%20%3D%20matches.radiant_win)%20win%2C%0Aplayer_matches.hero_id%2C%0Aplayer_matches.account_id%2C%0Aleagues.name%20leaguename%0AFROM%20matches%0AJOIN%20match_patch%20using(match_id)%0AJOIN%20leagues%20using(leagueid)%0AJOIN%20player_matches%20using(match_id)%0ALEFT%20JOIN%20notable_players%20using(account_id)%0ALEFT%20JOIN%20teams%20using(team_id)%0AJOIN%20heroes%20ON%20player_matches.hero_id%20%3D%20heroes.id%0AWHERE%20TRUE%0AAND%20notable_players.team_id%20%3D%20{0}".format(self.team_id)
    #     if self.patch:
    #         url += "%0AAND%20match_patch.patch%20%3D%20%27{0}%27".format(self.patch)
    #     if self.player_id:
    #         url += "%0AAND%20player_matches.account_id%20%3D%20%27{0}%27".format(self.player_id)
    #     if self.hero_id:
    #         url += "%0AAND%20player_matches.hero_id%20%3D%20%27{0}%27".format(self.hero_id)
    #     if self.start_time:
    #         url += "%0AAND%20matches.start_time%20%3D%20%27{0}%27".format(self.start_time)
    #     if self.end_time:
    #         url += "%0AAND%20matches.start_time%20%3D%20%27{0}%27".format(self.end_time)
    #     if self.league_id:
    #         url += "%0AAND%20matches.le agueid%20%3D%20%27{0}%27".format(self.league_id)
    #     url += "%0AORDER%20BY%20matches.match_id%20DESC%20NULLS%20LAST%0ALIMIT%20200"
    #     match_ids_resp = request_(url)
    #     self.match_ids = set(x["match_id"] for x in json.loads(match_ids_resp)["rows"])

    # def add_matches(self):
    #     """
    #     We need to store what heros are on our team, to allow for easier replay parsing/choosing what ticks apply to us
    #     :return:
    #     """
    #
    #     for match_id in self.match_ids:
    #         match = Match(match_id)
    #         if not self.only_download:
    #             # No sleep time because the Match() object sleeps for 1 second for its own API requests
    #             match_details = json.loads(get_match_details(match_id, APIKEY, sleep_time=0))["result"]
    #             if match_details["radiant_team_id"] == self.team_id:
    #                 match.add_side(True)
    #             elif match_details["dire_team_id"] == self.team_id:
    #                 match.add_side(False)
    #             else:
    #                 raise Exception("Team is not in this match")
    #
    #             for pick in match_details["picks_bans"]:
    #                 if not pick["is_pick"]:
    #                     continue
    #                 else:
    #                     # Dont think I can use fancy bit operators as one is True/False. One 0/1
    #                     # if match_id == 3117431107:
    #                     #     import pdb; pdb.set_trace()
    #                     radiant_pick = match_details["radiant_team_complete"] == pick["team"]  # pick["team"] seems to be slot. not side
    #                     if (match.is_radiant and radiant_pick) or (not radiant_pick and not match.is_radiant):
    #                         match.add_hero(pick["hero_id"])
    #         self.matches.add(match)
    #         self.matches_by_id[match.id] = match

    def download_replays(self):
        """
        Use thread pool to download some replays in parallel
        Does seem to save time
        :return:
        """
        print("Downloading replays. May take a while")
        try:
            # TODO Hmmmm this didnt wait for them all to finish. Bug where last few were still zipped
            with futures.ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
                executor.map(download_and_extract, self.matches, timeout=600)
        except:
            traceback.print_exc()
            print("A replay failed to download. Please try again")
            exit()

        print("Downloads finished")

    def parse_replays(self):
        """
        Use clarity dota2 replay parser with slightly custom scripts
        Parse all replays at once (Java slower when start-up. Has compiled functions and stuff by later replays)

        We dont catch stderr, so it will just print to console/shell
        :return: generator of std_out
        """
        jar = os.path.normpath("%s/target/%s.one-jar.jar" % (CLARITY_FOLDER, self.search_phrase))
        files = [os.path.normpath("%s/%d.dem" % (REPLAY_FOLDER, match.id)) for match in self.matches]
        p = subprocess.Popen(["java", "-jar", jar] + files, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return codecs.iterdecode(p.stdout, 'utf8')

    def iterate_matches(self, heroes_dict):
        """
        :param heroes_dict:
        :return: Generator that yields the strings for result output
        """

        if self.only_download:
            for match in self.matches:
                yield "Match %d\n" % match.id
        else:
            contents = self.parse_replays()

            match_id_regex = re.compile(r"^\((\d+)\)")

            for line in contents:
                match_id_maybe = match_id_regex.findall(contents) if self.multiline else match_id_regex.findall(line)
                if not match_id_maybe:
                    continue

                match_id = int(match_id_maybe[0])
                self.find_interesting_ticks(line, self.match_from_id(match_id), heroes_dict)

            for match in sorted(self.matches, key=lambda x: x.id):  # TODO which way sorting makes more sense?
                yield "Match %d: " % match.id
                for tick in sorted(match.interesting_ticks):
                    yield "%d, " % tick
                yield '\n'

    def find_interesting_ticks(self, line, match, heroes_dict):
        """
        Override in base class
        :param line:
        :param match:
        :param heroes_dict:
        :return:
        """
        raise NotImplemented()


class SmokeSearch(Search):

    def __init__(self, team_id, only_download, patch=None, time_range=None, tick_offset=60):
        super().__init__(team_id, only_download, patch, time_range, tick_offset)
        self.search_phrase = "smoketimings"

    def find_interesting_ticks(self, line, match, heroes_dict):
        """

        :param line: String. log line from java parser
        :param match: Match
        :param heroes_dict:
        :return:
        """
        # Cannot match on uses smoke of deceit. as if used by courier this line doesnt exist
        smokes = re.search("\[(\d+)\] ([^\s]+) receives modifier_smoke_of_deceit buff/debuff from", line)
        if smokes:
            tick, hero = smokes.groups()
            tick = int(tick)
            tick -= self.tick_offset  # Allow to move to few seconds before the action
            try:
                hero_id = heroes_dict[hero]["id"]
            except KeyError:  # dumb illusion or some bullshit. we'll catch a real hero on further loops
                return
            if hero_id in match.our_heroes:
                match.interesting_ticks.add(tick)


class CourierKillSearch(Search):

    def __init__(self, team_id, only_download, patch=None, time_range=None, tick_offset=60):
        super().__init__(team_id, only_download, patch, time_range, tick_offset)
        self.search_phrase = "courierkills"
        self.search_phrase = "smoketimings"

    def find_interesting_ticks(self, line, match, heroes_dict):
        """

        :param line: String. log line from java parser
        :param match: Match
        :param heroes_dict:
        :return:
        """
        courier_kills = re.search("\[(\d+)\] npc_dota_courier is killed by ([^\s]+)", line)
        if courier_kills:
            tick, hero = courier_kills.groups()
            tick = int(tick)
            tick -= self.tick_offset  # Allow to move to few seconds before the action
            try:
                hero_id = heroes_dict[hero]["id"]
            except KeyError:  # illusion/tower/`something else` kills courier
                return
            if hero_id in match.our_heroes:
                match.interesting_ticks.add(tick)


class MultikillSearch(Search):

    def __init__(self, team_id, only_download, patch=None, time_range=None, tick_offset=60, num_kills=2, odota_file=None):
        super().__init__(team_id, only_download, patch, time_range, tick_offset, odota_file)
        self.search_phrase = "multikills"
        self.search_phrase = "smoketimings"
        self.num_kills = num_kills
        assert self.num_kills < 9
        #self.multiline = True

    def find_interesting_ticks(self, line, match, heroes_dict):
        """

        :param line: String. log line from java parser
        :param match: Match
        :param heroes_dict:
        :return:
        """

        # Ignore pycharm error, doesnt understand the string replacement
        multi_kills = re.search(
            "\[(\d+)\] ([^\s]+) performs multikill of %d" % self.num_kills,
            line
        )
        # multi_kills = re.search(
        #     "(?s)type: DOTA_COMBATLOG_MULTIKILL.*?value: (%d).*?\[(\d+)\] [^\s]+ is killed by ([^\s]+)" % self.num_kills,
        #     line
        # )
        if multi_kills:
            tick, hero = multi_kills.groups()
            tick = int(tick)
            tick -= self.tick_offset  # Allow to move to few seconds before the action
            try:
                hero_id = heroes_dict[hero]["id"]
            except KeyError:  # illusion/tower/`something else` kills courier
                return
            if hero_id in match.our_heroes:
                match.interesting_ticks.add(tick)
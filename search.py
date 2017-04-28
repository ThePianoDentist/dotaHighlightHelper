import codecs
import json
import re
import subprocess
import traceback
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from multiprocessing.pool import Pool

from api_requests import download_and_extract, download_, extract_
from constants import *
from match import Match


class Search(object):

    def __init__(self, tick_offset=60, odota_file=None):
        """

        :param tick_offset:
        :param odota_file:
        """
        # TODO what is reasonable timerange
        self.matches_by_id = {}
        self.search_phrase = None
        self.matches = set()
        self.tick_offset = tick_offset
        self.multiline = False
        self.odota_file = odota_file

    def match_from_id(self, match_id):
        """
        :rtype: Match
        """
        return self.matches_by_id[match_id]

    def find_match_ids_odota(self):
        with open(self.odota_file) as f:
            data = json.load(f)
        for match_info in data:
            if match_info["match_id"] not in self.matches_by_id:
                new_match = Match(match_info["match_id"])
                self.matches.add(new_match)
                self.matches_by_id[new_match.id] = new_match
            new_match.add_hero(match_info["hero_id"])

    def download_replays(self):
        """
        Use multiprocessing pool to download a few in parallel
        Does seem to save time
        :return:
        """
        print("Downloading replays. May take a while")
        pool = Pool()
        pool.map(download_and_extract, self.matches)

        # with ThreadPoolExecutor(max_workers=3) as executor:
        #     executor.map(download_and_extract, self.matches, timeout=600)
        # for match in self.matches:
        #     try:
        #         print("doing match: %d" % match.id)
        #         extract_(match)
        #     except:
        #         print("failed: %d" % match.id)
        #         traceback.print_exc()
        #         continue
        # below was put in to catch exceptions. but generated a weird exception itself on successful runs
        # for future in as_completed(futures):
        #     print(future)

        print("Downloads finished for matches: \n%s" % ",".join([str(x.id) for x in self.matches]))

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

    def __init__(self, tick_offset=60, odota_file=None):
        super().__init__(tick_offset, odota_file)
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

    def __init__(self, tick_offset=60, odota_file=None):
        super().__init__(tick_offset, odota_file)
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

    def __init__(self, tick_offset=60, num_kills=2, odota_file=None):
        super().__init__(tick_offset, odota_file)
        self.search_phrase = "multikills"
        self.search_phrase = "smoketimings"
        self.num_kills = num_kills
        assert 1 < self.num_kills < 9

    def find_interesting_ticks(self, line, match, heroes_dict):
        """

        :param line: String. log line from java parser
        :param match: Match
        :param heroes_dict:
        :return:
        """

        multi_kills = re.search(
            "\[(\d+)\] ([^\s]+) performs multikill of %d" % self.num_kills,
            line
        )

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
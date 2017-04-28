import codecs
import json
import re
import subprocess
import traceback
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from multiprocessing.pool import Pool

from api_requests import download_and_extract
from constants import *
from match import Match


class Search(object):

    def __init__(self, tick_offset=60, odota_file=None, expected_hero_count=None):
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
        self.expected_hero_count = expected_hero_count

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

        if self.expected_hero_count:
            # TODO could probably do this check whilst adding matches
            # Have to watch out for obvious solutions missing off check of last match
            for match in self.matches:
                if len(match.our_heroes) != self.expected_hero_count:
                    raise Exception(
                        "Expected %d heroes to be searching over per game. Found %d" % (
                            len(match.our_heroes), self.expected_hero_count)
                    )

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

        # TODO if we need a multiline check must update this
        for line in contents:
            j_line = json.loads(line)

            match_id = j_line["matchID"]#int(match_id_maybe[0])
            self.find_interesting_ticks(j_line, self.match_from_id(match_id), heroes_dict)

        for match in sorted(self.matches, key=lambda x: x.id):  # TODO which way sorting makes more sense?
            yield "Match %d: " % match.id
            for tick in sorted(match.interesting_ticks):
                yield "%d, " % tick
            yield '\n'

    def find_interesting_ticks_line(self, j_line, match, heroes_dict):
        """
        Override in base class
        :param line: json dictionary representing the log line coming from odota Parse
        :param match:
        :param heroes_dict:
        :return:
        """
        raise NotImplemented()

    def find_interesting_ticks(self, contents, match, heroes_dict):
        """
        Override in base class
        :param line: json dictionary representing the log line coming from odota Parse
        :param match:
        :param heroes_dict:
        :return:
        """
        raise NotImplemented()


class SmokeSearch(Search):

    def __init__(self, tick_offset=60, odota_file=None):
        super().__init__(tick_offset, odota_file)
        self.search_phrase = "smoketimings"

    # Surely this indicates Ive designed things wrong?
    def find_interesting_ticks(self, j_line, match, heroes_dict):
        return self.find_interesting_ticks_line(j_line, match, heroes_dict)

    def find_interesting_ticks_line(self, j_line, match, heroes_dict):
        """

        :param line: String. log line from java parser
        :param match: Match
        :param heroes_dict:
        :return:
        """
        # Cannot match on uses smoke of deceit. as if used by courier this line doesnt exist
        # targethero True condition as only care about heroes. dont care about illusions/minions smoked
        if j_line["type"] == "DOTA_COMBATLOG_MODIFIER_ADD" and j_line["inflictor"] == "modifier_smoke_of_deceit"\
                and j_line["targethero"]:
            hero = j_line["targetname"]
            hero_id = heroes_dict[hero]["id"]
            tick = j_line["tick"]
            tick -= self.tick_offset  # Allow to move to few seconds before the action
            if hero_id in match.our_heroes:
                match.interesting_ticks.add(tick)


class CourierKillSearch(Search):

    def __init__(self, tick_offset=60, odota_file=None):
        super().__init__(tick_offset, odota_file)
        self.search_phrase = "courierkills"
        self.search_phrase = "smoketimings"

    # Surely this indicates Ive designed things wrong?
    def find_interesting_ticks(self, j_line, match, heroes_dict):
        return self.find_interesting_ticks_line(j_line, match, heroes_dict)

    def find_interesting_ticks_line(self, j_line, match, heroes_dict):
        """

        :param line: String. log line from java parser
        :param match: Match
        :param heroes_dict:
        :return:
        """
        # TODO could we catch/handle when courier gets killed by forge spirits/boars/minions etc
        if j_line["type"] == "DOTA_COMBATLOG_DEATH" and j_line["targetname"] == "npc_dota_courier"\
                and j_line["attackerhero"]:
            hero = j_line["attackername"]
            hero_id = heroes_dict[hero]["id"]
            tick = j_line["tick"]
            tick -= self.tick_offset  # Allow to move to few seconds before the action
            if hero_id in match.our_heroes:
                match.interesting_ticks.add(tick)


class MultikillSearch(Search):

    def __init__(self, tick_offset=60, num_kills=2, odota_file=None):
        super().__init__(tick_offset, odota_file)
        self.search_phrase = "multikills"
        self.search_phrase = "smoketimings"
        self.num_kills = num_kills
        assert 1 < self.num_kills < 9

    def find_interesting_ticks(self, j_line, match, heroes_dict):
        """

        :param line: String. log line from java parser
        :param match: Match
        :param heroes_dict:
        :return:
        """

        if j_line["type"] == "DOTA_COMBATLOG_MULTIKILL" and j_line["value"] == self.num_kills:
            hero = j_line["attackername"]
            hero_id = heroes_dict[hero]["id"]
            tick = j_line["tick"]
            tick -= self.tick_offset  # Allow to move to few seconds before the action
            if hero_id in match.our_heroes:
                match.interesting_ticks.add(tick)


class TeamwipeSearch(Search):
    """
    Find instances of teamwiping the enemy team.
    Input should be an odota search based on team
    """

    def __init__(self, tick_offset=60, num_kills=2, odota_file=None):
        super().__init__(tick_offset, odota_file, expected_hero_count=5)
        self.search_phrase = "multikills"
        self.search_phrase = "smoketimings"
        self.num_kills = num_kills
        assert 1 < self.num_kills < 9
        self.multiline = True

    def find_interesting_ticks(self, j_line, match, heroes_dict):
        """

        :param line: String. log line from java parser
        :param match: Match
        :param heroes_dict:
        :return:
        """

        if j_line["type"] == "DOTA_COMBATLOG_MULTIKILL" and j_line["value"] == self.num_kills:
            hero = j_line["attackername"]
            hero_id = heroes_dict[hero]["id"]
            tick = j_line["tick"]
            tick -= self.tick_offset  # Allow to move to few seconds before the action
            if hero_id in match.our_heroes:
                match.interesting_ticks.add(tick)
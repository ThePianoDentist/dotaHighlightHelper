import codecs
import copy
import csv
import json
import os
import re
import subprocess
from concurrent import futures
from json import JSONDecodeError

import time

import constants
from api_requests import download_and_extract, postjson_request_, request_
from match import Match


class Search(object):

    def __init__(self, query_file, tick_offset, expected_hero_count=None):
        """

        :param tick_offset: how far before event to log it (seconds)
        :param odota_file:
        """
        # TODO what is reasonable timerange
        self.matches_by_id = {}
        self.search_phrase = None
        self.matches = set()
        self.tick_offset = tick_offset
        self.multiline = False
        self.query_file = query_file
        self.query_datdota = query_file.endswith('csv')  # assuming csv for datdota. json for odota. Im sure this isnt good
        self.expected_hero_count = expected_hero_count

    def match_from_id(self, match_id):
        """
        :rtype: Match
        """
        return self.matches_by_id[match_id]

    def find_match_ids(self):
        self.find_match_ids_datdota() if self.query_datdota else self.find_match_ids_odota()
        if self.expected_hero_count:
            # TODO could probably do this check whilst adding matches
            # Have to watch out for obvious solutions missing off check of last match
            for match in self.matches:
                if len(match.our_heroes) != self.expected_hero_count:
                    raise Exception(
                        "Expected %d heroes to be searching over per game. Found %d" % (
                            len(match.our_heroes), self.expected_hero_count)
                    )

    def find_match_ids_odota(self):
        with open(self.query_file) as f:
            data = json.load(f)
        for match_info in data:
            if match_info["match_id"] not in self.matches_by_id:
                new_match = Match(match_info["match_id"])
                self.matches.add(new_match)
                self.matches_by_id[new_match.id] = new_match
            new_match.add_hero(match_info["hero_id"])

    def find_match_ids_datdota(self):
        with open(self.query_file) as f:

            def remove_bom(line):
                return line.lstrip("ï»¿")

            reader = csv.DictReader((remove_bom(line) for line in f), delimiter=',')
            for i, match_info in enumerate(reader):
                read_match_id = int(match_info["Match ID"])
                if read_match_id not in self.matches_by_id:
                    new_match = Match(read_match_id)
                    self.matches.add(new_match)
                    self.matches_by_id[new_match.id] = new_match
                with open("hero_ids.json") as f_heroes:
                    heroes = json.load(f_heroes)
                for _, hero in heroes.items():
                    # Try and be safe from datdota hero names not quite matching localized names in json constants
                    if ''.join([j.lower() for j in hero["localized_name"] if j.isalpha()]) == ''.join([j.lower() for j in match_info["Hero"] if j.isalpha()]):
                        new_match.add_hero(hero["id"])
                        break

    def get_download_urls(self):
        request_data = json.dumps({"contents": [m.id for m in self.matches if not m.already_have_replay]})
        try:
            result = json.loads(postjson_request_("http://37.97.239.48:8000/matches", request_data))
            for found in result["found"]:
                match = self.matches_by_id[found["id"]]
                match.replay_url = found["url"]
            for failed in result["failed"]:  # use opendota as a fallback
                match = self.matches_by_id[failed]
                match.replay_url = match.generate_replay_url()
        except:  # my server is probably down or borken
            for match in self.matches:
                match.replay_url = match.generate_replay_url()

    def download_replays(self):
        """
        Use multiprocessing pool to download a few in parallel
        Does seem to save time
        :return:
        """
        # TODO make sure other processes cleaned up if this one gets killed
        self.get_download_urls() # Get the urls first
        print("Downloading replays. May take a while")
        start = time.time()
        with futures.ThreadPoolExecutor(max_workers=constants.MAX_DOWNLOAD_THREADS) as executor:
            executor.map(download_and_extract, self.matches, timeout=600)
        print("Have all replays. Took: %d seconds" % (time.time() - start))

    def parse_replays(self):
        """
        Use clarity dota2 replay parser with slightly custom scripts
        Parse all replays at once (Java slower when start-up. Has compiled functions and stuff by later replays)

        We dont catch stderr, so it will just print to console/shell
        :return: generator of std_out
        """
        jar = os.path.normpath(constants.ODOTA_REPLAY_PARSER_FILE)
        files = [os.path.normpath("%s/%d.dem" % (constants.REPLAY_FOLDER, match.id)) for match in self.matches]
        p = subprocess.Popen(["java", "-jar", jar] + files, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return codecs.iterdecode(p.stdout, 'utf8')

    def iterate_matches(self, heroes_dict):
        """
        The java parses all the matches at the same time (up to thread pool limit)
        Therefore contents has a mix of all of them
        We yield a match's results as soon as we know it's finished parsing
        :param heroes_dict:
        :return: Generator that yields the strings for result output
        """
        contents = self.parse_replays()

        for ended_match in self.find_interesting_ticks(contents, heroes_dict):
            yield "Match %d: " % ended_match.id
            for tick in sorted(ended_match.interesting_ticks):
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

    def find_interesting_ticks(self, contents, heroes_dict):
        """

        :param contents: line-stream (is that right term?) from log of java replay parsing
        :param heroes_dict: to translate hero name in dota-code to its id
        :return: yield a match object, only when it has finished parsing
        """
        for line in contents:
            if line is None:
                break
            ended = re.search("\[(\d+)\] total time taken", line)
            if ended:
                ended_match = int(ended.group(1))
                yield self.match_from_id(ended_match)

            try: # TODO strip out all the blank lines
                j_line = json.loads(line)
            except JSONDecodeError:  # if its not json. dont care about it
                continue

            match_id = j_line["matchID"]
            self.find_interesting_ticks_line(j_line, match_id, heroes_dict)

    @staticmethod
    def get_modifier_counts(match_data, modifier_find_func, filter_func):
        current_event = None
        events = []
        for entry in match_data:
            if modifier_find_func(entry):
                current_event = current_event or {'tick': entry["tick"], 'number': 0}
                current_event["number"] += 1
            elif entry["type"] == "interval":
                if current_event:
                    events.append(copy.deepcopy(current_event))
                    current_event = None

        # Filter out fights we dont care about
        return filter(filter_func, events)

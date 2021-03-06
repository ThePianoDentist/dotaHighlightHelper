import json
from collections import defaultdict
from json import JSONDecodeError

import copy

import re

from search import Search


class ChronoSearch(Search):
    """
       Algorithms/ideas taken from here: https://github.com/odota/core/blob/master/processors/processTeamfights.js
       Teamfight cooldown in seconds. cant be ticks as what if pause during fight
    """

    def __init__(self, odota_file, tick_offset, min_enemies_caught=3):
        super().__init__(odota_file, tick_offset)
        self.search_phrase = "chronos"
        self.min_enemies_caught = min_enemies_caught

    def find_interesting_ticks(self, contents, heroes_dict):
        """

        :param line: String. log line from java parser
        :param match: Match
        :param heroes_dict:
        :return:
        """
        d = defaultdict(list)
        for line in contents:
            ended = re.search("\[(\d+)\] total time taken", line)
            if ended:
                match_id = int(ended.group(1))
                match_data = d[match_id]
                match = self.match_from_id(match_id)

                def is_chrono_entry(entry):
                    # TODO this will currently count team-mates as well. need to somewhere pull out what heroes are enemies
                    return entry["type"] == 'DOTA_COMBATLOG_MODIFIER_ADD' and \
                           entry["inflictor"] == "modifier_faceless_void_chronosphere_freeze" and\
                           entry["attackername"] == "npc_dota_hero_faceless_void" and entry["targethero"]\
                           and not entry["targetillusion"]

                chronos = self.get_modifier_counts(match_data, is_chrono_entry,
                                                      lambda event: event["number"] >= self.min_enemies_caught)

                # I dont think care about end tick right now. not going to skip to the end
                # However may want extending to also have in future
                match.interesting_ticks.update((chrono["tick"] - self.tick_offset) for chrono in chronos)
                del d[match_id]
                yield self.match_from_id(match_id)
            try:
                j_line = json.loads(line)
            except JSONDecodeError:
                continue
            d[j_line["matchID"]].append(j_line)
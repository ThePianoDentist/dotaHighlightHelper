import json
from collections import defaultdict
from json import JSONDecodeError

import re

import collections

import copy

from search import Search


class Teamfight(object):

    #TODO do I want all the extra stuff processTeamfights.js has in it?
    def __init__(self, start):
        self.start = start
        self.end = None
        self.deaths = 0
        self.enemy_deaths = 0

    # just to make some code more readable
    @property
    def last_death(self):
        return self.end


class TeamfightSearch(Search):
    """
       Algorithms/ideas taken from here: https://github.com/odota/core/blob/master/processors/processTeamfights.js
       Teamfight cooldown in seconds. cant be ticks as what if pause during fight
    """

    def __init__(self, odota_file, tick_offset, min_num_kills=3, min_num_enemy_kills=0, teamfight_cooldown=15,
                 expected_hero_count=None):
        super().__init__(odota_file, tick_offset, expected_hero_count=expected_hero_count)
        self.search_phrase = "teamfights"
        self.min_num_kills = min_num_kills
        self.min_num_enemy_kills = min_num_enemy_kills
        self.teamfight_cooldown = teamfight_cooldown

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

                current_teamfight = None
                teamfights = []
                for entry in match_data:
                    # DOTA_COMBATLOG_DEATH is 'killed' in the processTeamFight.js. is there extra manipulation
                    # between clarity output and this js? i.e. another js file entries are processed through
                    if entry["type"] == 'DOTA_COMBATLOG_DEATH' and entry["targethero"] and not entry["targetillusion"]:
                        current_teamfight = current_teamfight or Teamfight(entry["tick"])
                        current_teamfight.deaths += 1
                        End = collections.namedtuple('End', 'tick time')
                        current_teamfight.end = End(tick=entry["tick"], time=entry["time"])  # TODO something better than tuple?
                        if heroes_dict[entry["targetname"]]["id"] not in match.our_heroes:
                            current_teamfight.enemy_deaths += 1
                    elif entry["type"] == "interval":
                        if current_teamfight and entry["time"] - current_teamfight.last_death.time > self.teamfight_cooldown:
                            teamfights.append(copy.deepcopy(current_teamfight))
                            current_teamfight = None

                # Filter out fights we dont care about
                teamfights = [tf for tf in teamfights if
                              tf.deaths >= self.min_num_kills and tf.enemy_deaths >= self.min_num_enemy_kills]

                # I dont think care about end tick right now. not going to skip to the end
                # However may want extending to also have in future
                match.interesting_ticks.update((tf.start - self.tick_offset) for tf in teamfights)
                del d[match_id]  # DO I need to do this? does it get garbage collected anyway. shouldm check memory usage
                yield self.match_from_id(match_id)
            try:
                j_line = json.loads(line)
            except JSONDecodeError:
                continue
            d[j_line["matchID"]].append(j_line)


class TeamwipeSearch(TeamfightSearch):
    """
    Find instances of teamwiping the enemy team.
    Input should be an odota search based on team
    """

    def __init__(self, odota_file, tick_offset):
        super().__init__(odota_file, tick_offset, min_num_enemy_kills=5, expected_hero_count=5)
        self.search_phrase = "teamwipes"
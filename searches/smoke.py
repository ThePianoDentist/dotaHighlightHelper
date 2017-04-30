from search import Search


class SmokeSearch(Search):

    def __init__(self, odota_file, tick_offset):
        super().__init__(odota_file, tick_offset)
        self.search_phrase = "smoketimings"

    def find_interesting_ticks_line(self, j_line, match_id, heroes_dict):
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
            match = self.match_from_id(match_id)
            hero = j_line["targetname"]
            hero_id = heroes_dict[hero]["id"]
            tick = j_line["tick"]
            tick -= self.tick_offset  # Allow to move to few seconds before the action
            if hero_id in match.our_heroes:
                match.interesting_ticks.add(tick)
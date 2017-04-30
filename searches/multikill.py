from search import Search


class MultikillSearch(Search):

    def __init__(self, odota_file, tick_offset, min_multikill=2):
        super().__init__(odota_file, tick_offset)
        self.search_phrase = "multikills"
        self.num_kills = min_multikill
        assert 1 < self.num_kills < 9

    def find_interesting_ticks_line(self, j_line, match_id, heroes_dict):
        """

        :param line: String. log line from java parser
        :param match: Match
        :param heroes_dict:
        :return:
        """
        if j_line["type"] == "DOTA_COMBATLOG_MULTIKILL" and j_line["value"] == self.num_kills:
            match = self.match_from_id(match_id)
            hero = j_line["attackername"]
            hero_id = heroes_dict[hero]["id"]
            tick = j_line["tick"]
            tick -= self.tick_offset  # Allow to move to few seconds before the action
            if hero_id in match.our_heroes:
                match.interesting_ticks.add(tick)
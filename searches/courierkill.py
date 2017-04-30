from search import Search


class CourierkillSearch(Search):

    def __init__(self, odota_file, tick_offset):
        super().__init__(odota_file, tick_offset)
        self.search_phrase = "courierkills"

    def find_interesting_ticks_line(self, j_line, match_id, heroes_dict):
        """

        :param line: String. log line from java parser
        :param match: Match
        :param heroes_dict:
        :return:
        """
        # TODO could we catch/handle when courier gets killed by forge spirits/boars/minions etc
        if j_line["type"] == "DOTA_COMBATLOG_DEATH" and j_line["targetname"] == "npc_dota_courier"\
                and j_line["attackerhero"]:
            match = self.match_from_id(match_id)
            hero = j_line["attackername"]
            hero_id = heroes_dict[hero]["id"]
            tick = j_line["tick"]
            tick -= self.tick_offset  # Allow to move to few seconds before the action
            if hero_id in match.our_heroes:
                match.interesting_ticks.add(tick)
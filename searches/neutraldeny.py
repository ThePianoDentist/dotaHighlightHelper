from search import Search


class NeutraldenySearch(Search):

    def __init__(self, odota_file, tick_offset):
        super().__init__(odota_file, tick_offset)
        self.search_phrase = "neutraldenies"

    def find_interesting_ticks_line(self, j_line, match_id, heroes_dict):
        """

        :param line: String. log line from java parser
        :param match: Match
        :param heroes_dict:
        :return:
        """
        # TODO maybe also check recently damaged by an opponet. or check opponet coords to see if near?
        # people dont really deliberately suicide to respawn faster now so does this matter?
        if j_line["type"] == "DOTA_COMBATLOG_DEATH" and "neutral" in j_line["attackername"] and j_line["targethero"]:
            match = self.match_from_id(match_id)
            hero = j_line["targetname"]
            hero_id = heroes_dict[hero]["id"]
            tick = j_line["tick"]
            tick -= self.tick_offset  # Allow to move to few seconds before the action
            if hero_id in match.our_heroes:
                match.interesting_ticks.add(tick)
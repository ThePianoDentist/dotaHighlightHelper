import argparse
import json
import time

from constants import *


def command_line_options():
    # TODO Im having to add extra arguments for all the weird cases. maybe should just be user input, rather than command line args
    parser = argparse.ArgumentParser(description='Bulk download dota replays, plus analysis')
    parser.add_argument('odota_file', type=str, help="File-path of open-dota explorer json results")
    parser.add_argument("search_type", type=str, help='Search for this in replays. I.e. teamfights')
    parser.add_argument('--startOffset', "-o", default=10, type=float, dest="startOffset", help="Seconds before event to log")
    parser.add_argument('--list', '-l', dest="list", help='List search types available for use',
                        action='store_true')
    parser.add_argument('--onlyDownload', '-d', dest="onlyDownload", help='Only download replays. No analysis.',
                        action='store_true')
    parser.add_argument('--file', '-f', type=str, dest="out_file", help='File to save scripts results to')  # TODO check
    parser.add_argument('--minKills', '-k', default=3, type=int, dest="min_num_kills",
                        help='For teamfight searches, minimum number of kills to count as teamfight')
    parser.add_argument('--minEnemyKills', '-e', type=int, default=0, dest="min_num_enemy_kills",
                        help='For teamfight searches, minimum number of enemy kills to count as teamfight')
    parser.add_argument('--teamfightCooldown', '-t', type=int, default=15, dest="teamfight_cooldown",
                        help='For teamfight searches, how long between kills to class teamfight as over (seconds)')
    parser.add_argument('--minMultikill', '-m', type=int, default=2, dest="min_multikill",
                        help='Minimum number of kills for multikill search (i.e 5 is rampage, 4 ultrakill)')
    parser.add_argument('--minEnemiesCaught', '-c', type=int, default=3, dest="min_enemy_catch",
                        help='Minimum number of heores caught in chrono/rp/blackhole etc')
    args = parser.parse_args()
    # Believe dota2 runs at 30 ticks / seconds.
    # however it seems a bit off from this? it always seems to be way closer to the event than my startOffset
    tick_offset = args.startOffset * 30
    return args.odota_file, args.search_type, args.out_file, args.onlyDownload, args.list, tick_offset,\
           args.min_num_kills, args.min_num_enemy_kills, args.teamfight_cooldown, args.min_multikill, args.min_enemy_catch


def validate_input(odota_file, list_searches, search_type, only_download):
    if list_searches:
        print("Supported searches:\n")
        print("\n".join(ALLOWABLE_SEARCHES))
        exit()

    if not search_type and not only_download:
        print("Must specify either a search option, or --onlyDownload")
        exit()

    if search_type and search_type not in ALLOWABLE_SEARCHES:
        print("Specified an unsupported search operation")
        exit()

    if odota_file:
        return


def make_search(query_file, search_type, tick_offset, min_num_kills, min_num_enemy_kills, teamfight_cooldown, min_multikill, min_enemy_catch):
    """

    :param odota_file:
    :param search_type:
    :param tick_offset:
    :param min_num_kills:
    :param min_num_enemy_kills:
    :param teamfight_cooldown:
    :return: Instance of the search class for our query

    :rtype: Search
    """
    # TODO is this style going to get messy. I could use kwargs and just pass rubbish thats ignored by some searches?
    # TODO this dict lookup just makes it harder to read. we've already validated allowed. just call exact classes below?
    search_class = ALLOWABLE_SEARCHES[search_type]
    if search_type == "teamfights":
        return search_class(query_file, tick_offset, min_num_kills=min_num_kills,
                            min_num_enemy_kills=min_num_enemy_kills, teamfight_cooldown=teamfight_cooldown)
    elif search_type == "multikills":
        return search_class(query_file, tick_offset, min_multikill=min_multikill)
    elif search_type in ("chronos", "rps", "blackholes"):
        return search_class(query_file, tick_offset, min_enemies_caught=min_enemy_catch)
    else:
        return search_class(query_file, tick_offset)


def main():
    # This file comes from https://github.com/odota/dotaconstants
    with open("hero_ids.json") as f:  # TODO use constants package?
        heroes_dict = json.load(f)

    # TODO should add a flag to return times instead of ticks. as its trivial now using odota Parse.java
    query_file, search_type, out_file, only_download, list_searches, tick_offset, min_num_kills, min_num_enemy_kills, teamfight_cooldown, min_multikill, min_enemy_catch =\
        command_line_options()
    validate_input(query_file, list_searches, search_type, only_download)

    search = make_search(query_file, search_type, tick_offset, min_num_kills, min_num_enemy_kills, teamfight_cooldown, min_multikill, min_enemy_catch)
    search.find_match_ids()  #TODO this doesnt need to fully block downloading of first replays. can use generators?
    search.download_replays()
    if only_download:
        return

    print("Parsing replays")
    if out_file is not None:
        with open(out_file, "w") as f:
            for x in search.iterate_matches(heroes_dict):
                f.write(x)
    else:
        start = time.time()
        for x in search.iterate_matches(heroes_dict):
            print(x, end='')
        print("Time taken: %f" % (time.time() - start))

if __name__ == "__main__":
    main()

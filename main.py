import argparse
import json
import time

from constants import *
from search import SmokeSearch


def command_line_options():
    parser = argparse.ArgumentParser(description='Bulk download dota replays, plus analysis')
    parser.add_argument('team_id', type=int, help='TeamID of team to analyse')
    parser.add_argument('--patch', '-p', type=str, dest="patch", help='DotA patch number. I.e. 7.05')
    # TODO replace default of smoke timings when have others
    parser.add_argument('--search', '-s', default="smoketimings", type=str, dest="search_type",
                        help='Search for this in replays. I.e. teamfights')
    parser.add_argument('--tickOffset', default=2, type=float, dest="tickOffset", help="Seconds before event to log")
    parser.add_argument('--list', '-l', dest="list", help='List search types available for use',
                        action='store_true')
    parser.add_argument('--onlyDownload', '-d', dest="onlyDownload", help='Only download replays. No analysis.',
                        action='store_true')
    parser.add_argument('--file', '-f', type=str, dest="out_file", help='File to save scripts results to')  # TODO check
    args = parser.parse_args()
    return args.team_id, args.patch, args.search_type, args.out_file, args.onlyDownload, args.list, args.tickOffset


def validate_input(list_searches, search_type, only_download):
    if list_searches:
        print("Supported searches:\n")
        print("\n".join(ALLOWABLE_SEARCHES))
        exit()

    if not search_type and not only_download:
        print("Must specify either a search option (-s), or --onlyDownload")
        exit()

    if search_type not in ALLOWABLE_SEARCHES:
        print("Specified an unsupported search operation")
        exit()


def main():
    # This file comes from https://github.com/odota/dotaconstants
    with open("hero_ids.json") as f:  # TODO use constants package?
        heroes_dict = json.load(f)

    team_id, patch, search_type, out_file, only_download, list_searches, tick_offset = command_line_options()
    # args
    #team_id = 2108395 # TNC
    validate_input(list_searches, search_type, only_download)

    print("Searching for team: %d" % team_id)
    #search = make_search(search_type)
    search = SmokeSearch(team_id, only_download, patch=patch, tick_offset=tick_offset)

    search.find_match_ids()
    search.add_matches()
    search.download_replays()

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

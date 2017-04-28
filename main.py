import argparse
import json
import time

from constants import *
from search import SmokeSearch, MultikillSearch


def command_line_options():
    parser = argparse.ArgumentParser(description='Bulk download dota replays, plus analysis')
    parser.add_argument('-odota', '-o', dest='odota_file', type=str, help="File-path of open-dota explorer json results")
    parser.add_argument('--team', '-t', dest='team_id', type=int, help='TeamID of team to analyse')
    parser.add_argument('--patch', '-P', type=str, dest="patch", help='DotA patch number. I.e. 7.05')
    # TODO replace default of smoke timings when have others
    parser.add_argument('--player', '-p', type=str, dest="player", help='Player account ID')
    parser.add_argument('--hero', '-h', type=str, dest="hero_id", help='Hero ID')
    parser.add_argument('--start', '-s', type=str, dest="start_time", help='Start time (yyyy-mm-dd)')
    parser.add_argument('--end', '-e', type=str, dest="end_time", help='End time (yyyy-mm-dd)')
    parser.add_argument('--league', '-l', type=str, dest="league_id", help='Player account ID')

    parser.add_argument('--search', '-s', default="smoketimings", type=str, dest="search_type",
                        help='Search for this in replays. I.e. teamfights')
    parser.add_argument('--tickOffset', default=2, type=float, dest="tickOffset", help="Seconds before event to log")
    parser.add_argument('--list', '-l', dest="list", help='List search types available for use',
                        action='store_true')
    parser.add_argument('--onlyDownload', '-d', dest="onlyDownload", help='Only download replays. No analysis.',
                        action='store_true')
    parser.add_argument('--file', '-f', type=str, dest="out_file", help='File to save scripts results to')  # TODO check
    args = parser.parse_args()
    return args.odota_file, args.team_id, args.patch, args.search_type, args.out_file, args.onlyDownload, args.list,\
           args.tickOffset


def validate_input(odota_file, list_searches, search_type, only_download):
    if odota_file:
        return
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

    odota_file, team_id, patch, search_type, out_file, only_download, list_searches, tick_offset = command_line_options()
    # args
    #team_id = 2108395 # TNC
    validate_input(odota_file, list_searches, search_type, only_download)

    print("Searching for team: %d" % team_id)
    #search = make_search(search_type)
    search = SmokeSearch(team_id, only_download, patch=patch, tick_offset=tick_offset, odota_file=odota_file)
    search2 = MultikillSearch(team_id, only_download, patch=patch, tick_offset=tick_offset, odota_file=odota_file)
    search2.find_match_ids_odota()
    # search2.find_match_ids()
    # search2.add_matches()
    search2.download_replays()

    if out_file is not None:
        with open(out_file, "w") as f:
            for x in search2.iterate_matches(heroes_dict):
                f.write(x)
    else:
        start = time.time()
        for x in search2.iterate_matches(heroes_dict):
            print(x, end='')
        print("Time taken: %f" % (time.time() - start))

if __name__ == "__main__":
    main()

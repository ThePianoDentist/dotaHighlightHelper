import re
import subprocess
import time
from urllib.request import urlopen, Request, urlretrieve

from constants import *


def request_(req_url, sleep_time=None):
    if sleep_time is None:
        sleep_time = 1
    print("Requesting: %s" % req_url)
    request = Request(req_url)
    request.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36')
    response = urlopen(request)
    out = response.read().decode('utf8') # cos python3 is kind of stupid http://stackoverflow.com/questions/6862770/python-3-let-json-object-accept-bytes-or-let-urlopen-output-strings
    time.sleep(sleep_time)
    return out


def download_and_extract(match):
    if match.already_have_replay:
        return

    urlretrieve(match.replay_url, match.download_path)

    # p = subprocess.Popen(["powershell", "-Command", '"Invoke-WebRequest %s -OutFile \'%s\'"' % (req_url, file_path)],
    #                      stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    #                      stderr=subprocess.PIPE)
    # output, err = p.communicate()
    folder = re.search("(.*)[\\\\/]\d+.dem.bz2", match.download_path).group(1)
    # FUCKCICICKCINGNG WINDOWOSOSOWOSOS
    # TODO add other platform version. way to do without 7zip dep on windows as well?
    p = subprocess.Popen([SEVENZIP_PATH, "x", match.download_path, "-o%s" % folder], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True) #TODO check not security risk shell true (really didnt want to do 7zip stuff without it on)
    output, err = p.communicate()
    print("Match successfully downloaded: %d" % match.id)
    os.remove(match.download_path)  # Delete the old compressed replay file


def get_match_details(match_id, APIKEY, sleep_time=None):
    return request_(
        "http://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v0001?" \
        "key=%s&match_id=%s" % (APIKEY, match_id), sleep_time=sleep_time)
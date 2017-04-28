import bz2
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
    try:
        urlretrieve(match.replay_url, match.download_path)
    except ConnectionResetError:
        time.sleep(1)
        urlretrieve(match.replay_url, match.download_path)

    # p = subprocess.Popen(["powershell", "-Command", '"Invoke-WebRequest %s -OutFile \'%s\'"' % (req_url, file_path)],
    #                      stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    #                      stderr=subprocess.PIPE)
    # output, err = p.communicate()
    # TODO add other platform version. way to do without 7zip dep on windows as well?
    time.sleep(0.1)
    with open(match.file_path, 'wb') as newf, bz2.BZ2File(match.download_path) as oldf:
        for data in iter(lambda : oldf.read(100 * 1024), b''):
            newf.write(data)
    # p = subprocess.Popen([SEVENZIP_PATH, "x", match.download_path, "-o%s" % folder], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    #                      stderr=subprocess.PIPE, shell=True) #TODO check not security risk shell true (it really didnt want to do 7zip stuff without it on)
    # output, err = p.communicate()
    # print(err)  # alright windows. so it gets "ERROR: Unexpected end of data"...but thats out not err.
    # print(output)
    print("Match successfully downloaded: %d" % match.id)
    os.remove(match.download_path)  # Delete the old compressed replay file

def download_(match):
    print(match.id)
    print(match.already_have_replay)
    if match.already_have_replay:
        return

    urlretrieve(match.replay_url, match.download_path)
    print("Match successfully downloaded: %d" % match.id)


def extract_(match):
    if match.already_have_replay:
        return
    with open(match.file_path, 'wb') as newf, bz2.BZ2File(match.download_path) as oldf:
        for data in iter(lambda : oldf.read(100 * 1024), b''):
            newf.write(data)
    print("Match successfully extracted: %d" % match.id)
    os.remove(match.download_path)  # Delete the old compressed replay file


def get_match_details(match_id, APIKEY, sleep_time=None):
    return request_(
        "http://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v0001?" \
        "key=%s&match_id=%s" % (APIKEY, match_id), sleep_time=sleep_time)
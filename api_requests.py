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
    time.sleep(0.1)
    with open(match.file_path, 'wb') as newf, bz2.BZ2File(match.download_path) as oldf:
        for data in iter(lambda: oldf.read(100 * 1024), b''):
            newf.write(data)

    print("Match successfully downloaded: %d" % match.id)
    os.remove(match.download_path)  # Delete the old compressed replay file

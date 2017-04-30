import bz2
import os
import time
from urllib.request import urlopen, Request, urlretrieve


def request_(req_url, sleep_time=1):
    print("Requesting: %s" % req_url)
    request = Request(req_url)
    request.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36')
    response = urlopen(request)
    out = response.read().decode('utf8') # cos python3 is kind of stupid http://stackoverflow.com/questions/6862770/python-3-let-json-object-accept-bytes-or-let-urlopen-output-strings
    time.sleep(sleep_time)  # obey api rate limits
    return out


def download(match):
    succeeded = False
    tries = 0
    # TODO it would be nice to debug this.
    # Seems to be connection issues. maybe having parallel downloads is just frowned upon and I should remove pooling downloads
    sleeper = 2 ** tries  # whatever
    while not succeeded and tries < 10:
        try:
            urlretrieve(match.replay_url, match.download_path)
            succeeded = True
        except:
            tries += 1
            time.sleep(sleeper)
            continue


def extract(match):
    with open(match.file_path, 'wb') as newf, bz2.BZ2File(match.download_path) as oldf:
        for data in iter(lambda: oldf.read(100 * 1024), b''):
            newf.write(data)
            if not data:
                return

    print("Match successfully downloaded: %d" % match.id)
    os.remove(match.download_path)  # Delete the old compressed replay file


def download_and_extract(match):
    """

    :param match:
    :return: ...why did I do return 1? I dont think thats necessary
    """

    if match.already_have_replay:
        return

    download(match)
    time.sleep(0.1)
    extract(match)
    return
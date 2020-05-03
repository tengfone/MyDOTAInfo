from requests import get
from API_KEY import STEAM_API
import re

# PREFIX = 'U:1:'
SteamCommunity = "steamcommunity.com/id/"
BASE = 76561197960265728


# VanityURL = http://steamcommunity.com/id/vanityURL

def get32id(vanityURL):
    """
    Takes in steam community url either steamcommunity.com/id/XXXX or XXXX and convert to a Steam 32 ID
    :param vanityURL: type String. can be http or https or just the user ID (id/XXXXX)
    :return: an integer, Steam 32 ID
    """
    str(vanityURL)
    if SteamCommunity in vanityURL:
        p = re.compile("/id/(.*)")
        vanityURL = str(p.search(vanityURL).group(1)).replace("/", '')

    if vanityURL.startswith(SteamCommunity):
        vanityURL = vanityURL[len(SteamCommunity):]
    RESOLVE_URL = 'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key=%s&vanityurl=%s'
    if vanityURL == None:
        exit(1)
    else:
        vanityURL = vanityURL.replace("/", '')
        results = get(RESOLVE_URL % (STEAM_API, vanityURL))
        if results.status_code == 403:
            raise ValueError("Steam API Key is invalid")
        else:
            results.raise_for_status()
            data = results.json()
            if data['response']['success'] == 1:
                output = int(data['response']['steamid'])
                # if need prefix, just append PREFIX at the front of the output ID
                return output - BASE
            else:
                raise ValueError('Could not resolve vanity url: %s' % vanityURL)
                exit(1)

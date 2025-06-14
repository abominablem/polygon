# -*- coding: utf-8 -*-
"""
Created on Sat Nov 16 16:42:32 2024

@author: marcu
"""

import re
import requests

from cinemagoerng import web
from urllib.request import Request, urlopen

base_url_imdb = "https://www.imdb.com"
base_url_episodes = base_url_imdb + "/title/%s/episodes/"

def get_episodes_dict(title_id: str) -> dict:
    seasons = get_seasons_dict_old(title_id)

    episodes = {}
    for season in seasons.keys():
        episodes[season] = _get_episodes_from_season_url(seasons[season])

    return episodes

def _get_episodes_from_season_url(url: str) -> dict:
    rep_ep_template = "<article.*?episode-item-wrapper.*?<\/article>"
    rep_ep_fulltitle = '.*data-testid="slate-list-card-title".*title__text--reduced">(?P<full_title>.*?)<\/div>'
    rep_ep_number = "^S\d+.E(?P<episode>\d+).*$"
    rep_ep_title = "^S(?:\d+.E\d+ ∙ )?(?P<title>.*)$"
    rep_ep_release_date = '.*bYaARM">(.*?)<\/span>'
    rep_ep_title_id = '.*?data-testid="slate-list-card-title".*?href="\/title\/(?P<title_id>tt\d+)\/.*'
    # Note: it would also be possible to get the plot tag (synopsis) and IMDb
    # user rating from the current (16/11/24) episode template

    episodes_html = requests_get_with_headers(url)
    episodes_matches = {}
    episode_number_fallback = 1 # default episode number if one can't be parsed

    for m in re.finditer(rep_ep_template, episodes_html):
        ep_html = m.group(0)
        full_title = re.match(rep_ep_fulltitle, ep_html).group("full_title")
        try:
            ep_title = re.match(rep_ep_title, full_title).group("title")
        except AttributeError:
            # if there's an error parsing out the episode table, take the full
            # string instead
            ep_title = full_title

        ep_title_id = re.match(rep_ep_title_id, ep_html).group("title_id")
        ep_release_date = re.match(rep_ep_title_id, ep_html).group("title_id")

        if re.match(rep_ep_number, full_title) is None:
            ep_number = episode_number_fallback
            episode_number_fallback += 1
        else:
            ep_number = int(re.match(rep_ep_number, full_title).group("episode"))

        episodes_matches[ep_number] = {
            "title_id": ep_title_id,
            "title": ep_title,
            "episode": ep_number,
            "release_date": ep_release_date,
            }

    return episodes_matches


def get_seasons_dict_old(title_id: str) -> dict:
    url = base_url_episodes % title_id
    episodes_html = requests_get_with_headers(url)

    regex_match_seasons = '<a.*?data-testid="tab-season-entry".*?href="(?P<url>.*?)".*?>(?P<season>.*?)<\/a>'

    season_matches = {}
    for season_match in re.finditer(regex_match_seasons, episodes_html):
        season = season_match.group("season")
        url = season_match.group("url")

        # any non-numeric seasons e.g. "Unknown" are set to 0
        if not re.match("^\d+$", season):
            season = 0
        else:
            season = int(season)

        season_matches[season] = base_url_imdb + url

    return season_matches


def get_seasons_dict(title_id: str) -> dict:
    url = base_url_episodes % title_id
    episodes_html = requests_get_with_headers(url)

    regex_match_seasons = '<a.*?data-testid="tab-season-entry".*?href="(?P<url>.*?)".*?>(?P<season>.*?)<\/a>'

    season_matches = {}
    for season_match in re.finditer(regex_match_seasons, episodes_html):
        season = season_match.group("season")
        url = season_match.group("url")

        # case numeric seasons to integer
        if re.match("^\d+$", season):
            season = int(season)

        season_matches[season] = base_url_imdb + url

    return season_matches

def requests_get_with_headers(url):
    request = Request(url)
    request.add_header("User-Agent", web._USER_AGENT)
    if "graphql" in url:
        request.add_header("Content-Type", "application/json")
    with urlopen(request) as response:
        content: bytes = response.read()
    return content.decode("utf-8")


# title_id = "tt0436992"
# season_dict = get_seasons_dict(title_id)
# print(season_dict)

# episodes = _get_episodes_from_season_url('https://www.imdb.com/title/tt14688458/episodes/?season=1')
# print(episodes)
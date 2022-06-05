# -*- coding: utf-8 -*-
"""
Created on Sat Jun  4 20:32:58 2022

@author: marcu
"""
import re
import unidecode
import enchant

from base import prospero_db
import futil


def _get_group_simple_patterns(group):
    return prospero_db.regex_patterns.filter(
        filters = {"group": group}, return_cols = ["regex", "value"],
        case_insensitive = True)

def _match_simple_patterns(group, value):
    patterns = _get_group_simple_patterns(group)
    for index, expr in enumerate(patterns['regex']):
        if re.search(expr, value, re.IGNORECASE):
            return str(patterns['value'][index]).strip()

def build_regex_construct(re_dict):
    """ Convert a deconstructed regex matching dictionary to a constructed
    one. Each element of 'pattern' is a list of words or single regex expression.
    The corresponding index in 'optional' is whether a match within this list
    is required to match the overall expression or not."""
    if type(re_dict) != dict or re_dict["type"] != "regex_construct":
        return re_dict

    pattern = list(re_dict["pattern"].values())
    optional = re_dict["optional"]
    parse, value, regex_parts = [], [], []

    regex_start = r"^.*\b"
    regex_end = r"\b.*$"
    for i in range(len(pattern)):
        end = r")?\b\s*" if optional[i] else r")\b\s*"
        regex_parts.append(r"\s*\b(?:" + "|".join(pattern[i]) + end)

    for i in range(len(pattern)):
        # build the regex which will return the strings used to construct the
        # final value. To do this, make each non-capturing group a capturing
        # group in turn, while keeping all other group non-capturing.
        end = r")?\b\s*" if optional[i] else r")\b\s*"
        match_part = regex_start + "".join(regex_parts[:i])
        match_part += r"\s*\b(" + "|".join(pattern[i]) + end
        match_part += "".join(regex_parts[i+1:]) + regex_end
        value.append(match_part)
        parse.append(True)

    return {
        "pattern": regex_start + "".join(regex_parts) + regex_end,
        "value": value, "parse": parse, "type": "regex"
        }

def parse_match_dict(group, string):
    if group.lower() == "album":
        re_dict = rd #TODO replace with sql call

    for key in re_dict.keys():
        match_type = re_dict[key]["type"]

        if match_type == "regex_construct":
            re_dict[key] = build_regex_construct(re_dict[key])

        if re.match(re_dict[key]["pattern"], string, re.I):
            match_type = re_dict[key]["type"]
            if match_type == "string":
                return re_dict[key]["value"]
            elif match_type == "regex":
                result = []
                for i in range(len(re_dict[key]["value"])):
                    value = re_dict[key]["value"][i]
                    parse = re_dict[key]["parse"][i]
                    if parse:
                        parsed = re.search(value, string, re.I).group(1)
                        if not parsed is None: result.append(parsed)
                    else:
                        result.append(value)
                result = " ".join(result)
                result = " ".join(result.replace("No.", "No. ").split())
                result = futil.true_titlecase(result)
                return result
    return None

def parse_filename_pattern(filename):
    """
    Parameters
    ----------
    filename : str
        String to match pattern to.
    Returns
    -------
    dict
        Dictionary of matched group names and values.

    Match filenames to a defined pattern. If able to match, parse
    the filename and extract all named capture groups as a dictionary.
    Does not explicitly support nested capture groups.

    """
    for d in fd.values():
        if re.match(d["match_pattern"], filename, re.IGNORECASE):
            captures = re.search(
                d["parse_pattern"], filename, re.IGNORECASE).groupdict()
        else:
            continue

        if type(captures) != dict:
            continue

        for k in captures:
            if d["rematch_values"].get(k, False):
                new_v = suggest_value(k, captures[k])
                if new_v != "" and new_v is not None:
                    captures[k] = new_v
        return captures
    return {}


def match_keywords(composer, album, number = None):
    """ Match using composer + album + number = track, and composer + album =
    genre + year, using the renames_legacy table and then the renames table """
    if not number is None:
        filter_kwargs = dict(filters = {
            "composer": composer, "album": album, "number": number},
            return_cols = ["track"], distinct = True, case_insensitive = True)
        value_dict = prospero_db.renames_legacy.filter(**filter_kwargs)
        # If nothing returned, try the current renames table
        if len(value_dict) == 0:
            value_dict = prospero_db.renames.filter(**filter_kwargs)
    else:
        value_dict = {}

    filter_kwargs = dict(
        filters = {"composer": composer, "album": album},
        return_cols = ["genre", "year"], distinct = True, case_insensitive = True
        )
    value_dict_album = prospero_db.renames_legacy.filter(**filter_kwargs)
    # If nothing returned, try the current renames table
    if len(value_dict_album) == 0:
        value_dict_album = prospero_db.renames.filter(**filter_kwargs)

    value_dict.update(value_dict_album)

    for group, value in value_dict.items():
        if isinstance(value, list):
            # if there are multiple values, take the first non-Null or empty one
            value_dict[group] = next(v for v in value
                                     if v is not None and str(v).strip() != '')

    return value_dict

def _get_youtube_url(filename, do_word_check = False):
    """ For a given filename, tries to detect if it ends in a valid YouTube
    video ID. If it does, returns the corresponding URL. """

    youtube_prefix = "www.youtube.com/watch?v="
    #take the last word in the string since the id will always be 1 word
    youtube_id = filename.split()[-1]

    if len(youtube_id) < 11:
        return ""
    elif len(youtube_id) >= 12:
        #to account for old youtube-dl behaviour, where the filename
        #format was <video title>-<video id>
        youtube_id = (youtube_id[-11:] if youtube_id[-12] == "-"
                      else youtube_id)

    #test for a valid id format
    if not re.match("[0-9a-zA-Z_-]{11}", youtube_id):
        return ""

    if re.match("[a-zA-Z]{11}", youtube_id) and do_word_check:
        # test if the string is a dictionary word
        # covers the case that the video name ends in an 11 letter word
        # This has by far the largest performance impact, so is disabled by
        # default
        if enchant.Dict("en_GB").check(youtube_id):
            return ""

    return youtube_prefix + youtube_id

def _get_year(filename):
    #Match 4 digit number in between some kind of brackets, starting with
    #1 or 2. Always take the last match
    try:
        return re.findall("[\[\(\{]([12]\d{3})[\]\)\}]", filename)[-1]
    except IndexError:
        return ""



def suggest_value(group, filename):
    # Handle simple regex matching patterns from pattern -> value
    group = group.lower()
    simple_match = _match_simple_patterns(group, filename)
    match_dict = {group: simple_match}

    # remove empty values which may have better matches later
    for k in list(match_dict.keys()):
        v = match_dict[k]
        if v is None or v == "": del match_dict[k]

    if group in ["url", "artist url"]:
        match_dict.setdefault("url", _get_youtube_url(filename, do_word_check = True))
    elif group == "album":
        match_dict.setdefault(group, parse_match_dict(group, filename).strip())
    elif group == "year":
        match_dict.setdefault(group, _get_year(filename).strip())

    match_dict.setdefault(group, None)
    return match_dict[group]

# print(match_keywords(composer = "Richard Strauss", album = "Six Songs, Op. 68 (Brentano Lieder)", number = 1))

rd = {'1': {'pattern': '.*\\bSymphony No.\\s?\\d+\\b.*',
  'value': ['Symphony No. ', '.*Symphony No.\\s?(\\d+)\\b.*'],
  'parse': [False, True],
  'type': 'regex'},
 '2': {'pattern': '.*(?=.*\\bBeethoven\\b.*)(?=.*\\bEroica\\b.*).*',
  'value': 'Symphony No. 3 (Eroica)',
  'type': 'string'},
 '3': {'type': 'regex_construct',
  'pattern': {'1': ['String','Piano','Wind','Clarinet','Cello','Violin','Harp','Oboe','Bassoon','Trumpet','Horn'],
   '2': ['Trio','Quartet','Quintet','Sextet','Septet','Octet','Nonet','Decet','Sonata','Concerto'],
   '3': ['No.\\s?(\\d+)']},
  'optional': [False, False, True]},
 '4': {'pattern': '.*\\bBWV\\.?\\s?\\b(22[0-4]|2[01][0-9]|1[0-9]{2}|[1-9]?[0-9])\\b.*',
  'value': ['Cantata ', '.*\\bBWV\\.?\\s?\\b(22[0-4]|2[01][0-9]|1[0-9]{2}|[1-9]?[0-9])\\b.*'],
  'parse': [False, True],
  'type': 'regex'}}

fd = {'1': {'match_pattern': '(?!^.*?\\(.*? - .*?\\) Score Animation.*?$)^.*?\\s+\\(.*?\\)\\s+Score Animation\\s?(?:.{11})?$',
  'parse_pattern': '^(?P<track>.*?)\\s?\\((?P<composer>.*?)\\) Score Animation.*?$',
  'rematch_values': {'composer': True, "album": True}},
 '2': {'match_pattern': '^.*?\\s+\\(.*? - .*?\\)\\s+Score Animation\\s?(?:.{11})?$',
  'parse_pattern': '^(?P<track>.*?)\\s?\\((?P<album>.*)? - (?P<composer>.*?)\\) Score Animation.*?$',
  'rematch_values': {'composer': True}}}

# print(build_regex_construct(rd['3']))
print(parse_match_dict('album', 'Brahms - Trumpet Sextet No. 157 III. Moderato [abc Philhamonic Ochrestra]'))
print(suggest_value('album', "Lobe den Herrn, meine Seele (BWV 69 - J.S. Bach) Score Animation"))
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 12 20:21:02 2022

@author: marcu
"""
import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import re
from imdb import IMDb
from datetime import datetime

import constants as c
import futil as f
import base

imdb = IMDb()

def clean_id(imdb_id):
    """ Remove all non-numeric characters from the id, including
    leading "tt" """
    return re.sub("[^\d]", "", imdb_id)

def standardise_id(imdb_id):
    """ Standardise the given id with leading "tt" """
    imdb_id = str(imdb_id)
    if imdb_id[0:2] != "tt":
        return "tt" + imdb_id
    else:
        return imdb_id

class Title:
    def __init__(self, title_id = None, detail = None):
        if not title_id is None:
            self.clear()
            self._data_from_object(imdb.get_movie(clean_id(title_id)))

        if not detail is None:
            self.__dict__.update(detail)

    def refresh(self, detail = None):
        """ Update object based on latest IMDb data """
        self.clear()
        if detail is None:
            self._data_from_object(imdb.get_movie(clean_id(self.title_id)))
        else:
            self.__dict__.update(detail)

    def from_object(self, movie):
        """ Create Title object from imdb.Movie.Movie object """
        self._data_from_object(movie)

    def _data_from_object(self, movie):
        self.title_id = standardise_id(movie.getID())
        self._title = movie
        self._data = self._title.data

        self.type = self._data["kind"]

        if self.type == "episode":
            self.series_id = standardise_id(self._data["episode of"].getID())
            self.episode = self._data["episode"]
            self.season = self._data["season"]

        elif self.type in c.TV_TYPES:
            self.series_id = self.title_id
            self.get_episodes()

        self.title = self._data["title"]
        self.year = self._data_get("year", None)
        self.original_title = self._clean_original_title(
            self._data_get("original title", self.title), self.year
            )
        self.release_date = self._clean_release_date(
            self._data.get("original air date", None)
            )

        # private lists for use in get_tags
        # note tv series do not have directors (but episodes do)
        self._directors = self._get_names(self._data.get("director", []))
        self._genres = self._data.get("genres", [])
        self._writers = self._get_names(self._data.get("writer", []))

        self.director = ", ".join(self._directors)
        self.genre = ", ".join(self._genres)
        self.writer = ", ".join(self._writers)

        self.imdb_user_rating = self._data_get("rating", None)
        self.imdb_user_votes = self._data_get("votes", 0)

        self.runtime = f.list_default(
            self._data_get("runtimes", []), 0, None
            )

        self.plot_tag = f.list_default(
            self._data_get("plot", []), 0, ""
            )

    def get_episodes(self):
        if not self.type in c.TV_TYPES:
            raise WrongTitleTypeError(self.type)
        imdb.update(self._title, "episodes")

        # Create dictionary of Title object for each season/episode
        self.episodes = {}
        for season in self._data["episodes"]:
            self.episodes[season] = {}
            for episode in season:
                movie = self._data["episodes"][season][episode]
                self.episodes[season][episode] = Title().from_object(movie)
        return self.episodes

    def clear(self):
        """ Clear attributes """
        self.title_id = None
        self._title = None
        self._data = None
        self.type = None
        self.series_id = None
        self.episode = None
        self.season = None
        self.title = None
        self.original_title = None
        self.year = None
        self.release_date = None
        self._directors = []
        self._genres = []
        self._writers = []
        self.director = None
        self.genre = None
        self.writer = None
        self.imdb_user_rating = None
        self.imdb_user_votes = None
        self.runtime = None
        self.plot_tag = None

    def _data_get(self, key, default):
        """ Get data from imdb.Title.data object """
        return self._data.get(key, default)

    def get_dict(self, type = "title"):
        """ Get dictionary of values used in a given table """
        if type == "title":
            return_dict = self._get_dict(
                ["title_id", "type", "title", "original_title", "year",
                 "release_date", "director", "writer", "genre", "runtime",
                 "plot_tag", "imdb_user_rating", "imdb_user_votes"]
                )
        elif type == "series":
            return_dict = self._get_dict(
                ["series_id", "title", "type", "year", "genre", "plot_tag",
                 "imdb_user_rating", "imdb_user_votes"]
                )
        elif type == "episode":
            return_dict = self._get_dict(
                ["title_id", "series_id", "season", "episode"]
                )
        else:
            raise ValueError("Unrecognised title type")
        return return_dict

    def _get_dict(self, keys):
        return {key: self.__dict__[key] for key in keys}

    def get_tags(self, type = "title"):
        """ Return dictionary of title tags for fields which can take multiple
        values """
        if type == "title":
            return {
                "director": self._directors,
                "genre": self._genres,
                "writer": self._writers
                }
        elif type == "series":
            return {
                "genre": self._genres,
                }
        elif type == "episode":
            return {
                }
        else:
            raise ValueError("Unrecognised title type")


    def _clean_release_date(self, release_date):
        """ Parse dates of the form e.g. 12 Mar. 2020 """
        if release_date is None: return
        try:
            # extract the relevant bits (day/month/year) flexibly
            match_date = re.match(
                "^(?P<day>\d{1,2})\s(?P<month>[a-zA-Z]{3})\.?\s(?P<year>\d{4}).*$",
                release_date
                )
            # place into a consistent format for strptime
            parsed_date = datetime.strptime(
                "%s %s %s" % match_date.groups(),
                "%d %b %Y"
                )
            release_date = parsed_date.strftime("%Y-%m-%d")
        except:
            pass
        return release_date

    def get_series(self):
        """ Return Title object of parent series """
        if self.type == "episode":
            return Title().from_object(self._date["episode of"])
        elif self.type in c.TV_TYPES:
            return self
        else:
            raise WrongTitleTypeError(self.type)

    def _clean_original_title(self, original_title, year):
        """ Remove ' (XXXX)' from the end of the title where XXXX is the
        release year """
        if original_title[-7:] == " (%s)" % year:
            return original_title[:-7]
        else:
            return original_title

    def _get_names(self, people, firstn = 0):
        if not isinstance(people, list):
            people = [people]

        if firstn > 0:
            people = people[:firstn]

        names = [person.data['name'] for person in people]
        return names

    def __str__(self):
        if self.type == "episode":
            date = "??" if self.release_date is None else self.release_date
            return "%s : %s : %s S%02dE%02d %s (%s)" % (
                self.title_id, self.type,
                self._data["episode of"].get("title"), self.season,
                self.episode, self.title, date
                )
        elif self.type == "series":
            return "%s : %s : %s (%s)" % (
                self.title_id, self.type, self.title,
                self._data_get("series years", "??")
                )
        else:
            year = "??" if self.year is None else self.year
            return "%s : %s : %s (%s)" % (
                self.title_id, self.type, self.title, year
                )

class TitleExistsError(base.PolygonException):
    """ Raised when title already exists in database """
    def __init__(self):
        super().__init__("Title already exists in database")

class TitleNotExistsError(base.PolygonException):
    """ Raised when title doesn't exist in database """
    def __init__(self):
        super().__init__("Title does not exist in database")

class SeriesExistsError(base.PolygonException):
    """ Raised when series already exists in database """
    def __init__(self):
        super().__init__("Series already exists in database")

class SeriesNotExistsError(base.PolygonException):
    """ Raised when series doesn't exist in database """
    def __init__(self):
        super().__init__("Series does not exist in database")

class EpisodeExistsError(base.PolygonException):
    """ Raised when episode already exists in database """
    def __init__(self):
        super().__init__("Episode already exists in database")

class EpisodeNotExistsError(base.PolygonException):
    """ Raised when episode doesn't exist in database """
    def __init__(self):
        super().__init__("Episode does not exist in database")

class TagExistsError(base.PolygonException):
    """ Raised when tag combination already exists in database """
    def __init__(self):
        super().__init__("Tag already exists in database")

class WrongTitleTypeError(base.PolygonException):
    """ Raised when the given title has the wrong title type for the attempted
    operation """
    def __init__(self, title_type = None):
        super().__init__("Invalid title type for this operation")
        self.title_type = title_type


class IMDbFunctions:
    """ Container for function classes relating to specific tables, and
    functions relating to multiple tables """
    def __init__(self):
        self.titles = IMDbTitleFunctions()
        self.entries = IMDbEntryFunctions()
        self.entry_tags = IMDbEntryTagsFunctions()
        self.title_tags = IMDbTitleTagsFunctions()
        self.series = IMDbSeriesFunctions()
        self.episodes = IMDbEpisodesFunctions()
        self.db = base.polygon_db

    def exists(self, title):
        if isinstance(title, Title):
            title_id = title.title_id
        elif isinstance(title, str):
            title_id = title
        elif isinstance(title, dict):
            title_id = title["title_id"]
        else:
            raise ValueError("Unknown input type %s" % type(title))

        return self.titles.exists(title_id) or self.series.exists(title_id)

    def add_title(self, title):
        """ Add a new title/series to the correct table """
        if self.exists(title):
            return

        if isinstance(title, Title):
            pass
        elif isinstance(title, str):
            title = Title(title)
        elif isinstance(title, dict):
            title = Title(detail = title)
        else:
            raise ValueError("Unknown input type %s" % type(title))

        try:
            if title.type in c.TV_TYPES:
                self._add_series(title)
            elif title.type == "episode":
                self._add_episode(title)
            else:
                self._add_title(title)
        except TitleExistsError:
            raise

    def _add_episode(self, title):
        """ Test adding an episode and raise any errors that would occur. These
        are then handled in the front end by either importing or updating the
        series data """
        # check if the parent series exists in database
        if not self.series.exists(title):
            raise SeriesNotExistsError

        # check if the episode exists as a title in the database
        if not self.titles.exists(title):
            raise EpisodeNotExistsError

    def _add_series(self, title):
        """ Add a new series to the series table and add the episodes """
        try:
            self.series.add(title)
        except TitleExistsError:
            pass
        self.episodes.add(title)
        self.title_tags.add_dict(title.title_id, title.get_tags("series"))

    def _add_title(self, title):
        self.titles.add(title)
        self.title_tags.add_dict(title.title_id, title.get_tags("title"))

    def add_entry(self, imdb_id, tags = None, **kwargs):
        """ Add new entry to the entries table. """
        try:
            self.add_title(imdb_id)
        except TitleExistsError:
            pass
        self.entries.add(imdb_id, **kwargs)
        entry_id = max(self.entries.get_entry_id(title_id = imdb_id, **kwargs))
        # Expect tags in dictionary format of {tag_name: tag_value}. If
        # tag_name is None, assume tag_value is either a single tag or list
        # of tags to be added with NULL tag_name
        self.entry_tags.add_dict(entry_id, tags)

class IMDbEpisodesFunctions:
    """ Container for functions relating to the episodes table """
    def __init__(self):
        self.db = base.polygon_db.episodes

    def add(self, title):
        """ Add an episode or series of episodes to the database """
        if title.type in c.TV_TYPES:
            self._add_series_episodes(title)
        elif title.type == "episode":
            if self.exists(title):
                raise TitleExistsError
            self.db.insert(**title.get_dict("episode"))
        else:
            raise WrongTitleTypeError(title.type)

    def _add_series_episodes(self, title):
        """ Add all episodes in series to database (unless already present) """
        series = title.get_episodes()
        for season in series:
            for episode in season:
                if self.exists(episode):
                    pass
                else:
                    self.add(episode)

    def exists(self, title):
        """ Return if series exists in database """
        if isinstance(title, Title):
            title = title.title_id
        return self.exists_id(title)

    def exists_id(self, title_id):
        """ Return if title_id exists in database """
        result = self.db.filter({"title_id": title_id}, "title_id")
        return len(result["title_id"]) != 0

class IMDbSeriesFunctions:
    """ Container for functions relating to the series table """
    def __init__(self):
        self.db = base.polygon_db.series

    def add(self, title):
        """ Insert a series to the database if it does not already exist """
        if not title.type in c.TV_TYPES:
            raise WrongTitleTypeError(title_type = title.type)

        if self.exists(title):
            raise SeriesExistsError

        title_dict = title.get_dict("series")
        title_dict["import_date"] = self.db.getdate()
        self.db.insert(**title_dict)
        return title

    def update(self, imdb_id, detail):
        #TODO
        pass

    def exists(self, title):
        """ Return if series exists in database """
        if isinstance(title, Title):
            title = title.title_id
        return self.exists_id(title)

    def exists_id(self, series_id):
        """ Return if series_id exists in database """
        result = self.db.filter({"series_id": series_id}, "series_id")
        return len(result["series_id"]) != 0

class IMDbTitleTagsFunctions:
    """ Container for functions relating to the entry_tags table """
    def __init__(self):
        self.db = base.polygon_db.title_tags

    def add_dict(self,title_id, tag_dict):
        for tag_name, tags in tag_dict.items():
            if not isinstance(tags, list):
                tags = [tags]
            for tag_value in tags:
                self.add(title_id, tag_value, tag_name)

    def add(self, title_id, tag_value, tag_name = None):
        # tags should never be duplicated
        if self.exists(title_id, tag_value, tag_name):
            # raise TagExistsError
            return

        detail = dict(title_id = title_id, tag_value = tag_value)
        if not tag_name is None:
            detail["tag_name"] = tag_name

        self.db.insert(**detail)

    def exists(self, title_id, tag_value, tag_name = None):
        result = self.db.filter({"title_id": title_id,
                                 "tag_value": tag_value,
                                 "tag_name": tag_name}, "title_id")
        return len(result["title_id"]) != 0

class IMDbEntryTagsFunctions:
    """ Container for functions relating to the entry_tags table """
    def __init__(self):
        self.db = base.polygon_db.entry_tags

    def add_dict(self,entry_id, tag_dict):
        for tag_name, tags in tag_dict.items():
            if not isinstance(tags, list):
                tags = [tags]
            for tag_value in tags:
                self.add(entry_id, tag_value, tag_name)

    def add(self, entry_id, tag_value, tag_name = None):
        if self.exists(entry_id, tag_value, tag_name):
            raise TagExistsError

        detail = dict(entry_id = entry_id, tag_value = tag_value)
        if not tag_name is None:
            detail["tag_name"] = tag_name

        self.db.insert(**detail)

    def exists(self, entry_id, tag_value, tag_name = None):
        result = self.db.filter({"entry_id": entry_id,
                                 "tag_value": tag_value,
                                 "tag_name": tag_name}, "entry_id")
        return len(result["entry_id"]) != 0

class IMDbTitleFunctions:
    """ Container for functions relating to the Titles table """
    def __init__(self):
        self.db = base.polygon_db.titles

    def get(self, imdb_id, refresh = True):
        """ Get Title object. Optionally refresh from latest IMDb data."""
        if refresh:
            return Title(title_id = imdb_id)
        else:
            try:
                return Title(detail = self.get_detail(imdb_id))
            except TitleNotExistsError:
                return Title(title_id = imdb_id)

    def get_detail(self, imdb_id):
        """ Return dict of database values for an imdb_id """
        if not self.exists(imdb_id):
            raise TitleNotExistsError
        detail = self.db.filter({"imdb_id": imdb_id}, "*")
        return detail

    def add(self, title):
        """ Insert a title to the database if it does not already exist """
        if title.type in c.TV_TYPES:
            raise WrongTitleTypeError(title_type = title.type)

        title_dict = title.get_dict("title")
        title_dict["import_date"] = self.db.getdate()
        self.db.insert(**title_dict)
        return title

    def update(self, imdb_id, detail):
        #TODO
        pass

    def exists_id(self, imdb_id):
        """ Return if imdb_id exists in database """
        result = self.db.filter({"title_id": imdb_id}, "title_id")
        return len(result["title_id"]) != 0

    def exists(self, title):
        """ Return if title exists in database """
        if isinstance(title, Title):
            title = title.title_id
        return self.exists_id(title)

class IMDbEntryFunctions:
    """ Container for functions relating to the Entries table """
    def __init__(self):
        self.db = base.polygon_db.entries

    def add(self, title_id, entry_date, entry_order = None,
                  rating = None, rewatch = False, notes = ""):
        """ Insert a new entry row into entries table """
        if isinstance(title_id, Title):
            title_id = title_id.title_id
        detail = dict(
            title_id = title_id,
            entry_date = entry_date,
            rewatch = rewatch
            )

        # if the entry order is not specified, assume entries were logged
        # chronologically and add one to the maximum order
        if entry_order is None:
            detail["entry_order"] = self._get_entry_order(entry_date)
        else:
            self._offset_entries(entry_date, entry_order)
            detail["entry_order"] = entry_order

        if not rating is None: detail["rating"] = rating
        if not notes == "" and not notes is None: detail["notes"] = notes

        self.db.insert(**detail)

    def _offset_entries(self, entry_date, start, rollback = False):
        """ Offset all entry orders on a specific date greater than or equal to
        a certain order value up by one. For inserting a new entry in between
        two existing entries. In case the subsequent insert statement fails,
        also provide a rollback option to deincrement the entries. """
        operator = "-" if rollback else "+"
        self.db.execute(
            "UPDATE entries "
            "SET entry_order = entry_order %s 1" % operator +
            "WHERE entry_date = '%s' " % entry_date +
            "AND entry_order >= %s" % start
            )

    def _get_entry_order(self, entry_date):
        """ Get the next order number for an entry_date """
        rows = self.db.select("SELECT COUNT(*) FROM entries "
                              "WHERE entry_date = '%s'" % entry_date)
        return rows[0][0] + 1

    def get_entry_id(self, **kwargs):
        result = self.db.filter(kwargs, "entry_id")
        return result["entry_id"]


imdbf = IMDbFunctions()
imdbf.add_entry("tt2953050", rating = 6, notes = "Download",
                entry_date = "2022-01-19", tags = {"platform": "Download"})

base.polygon_db.close()
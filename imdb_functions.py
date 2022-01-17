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
        if detail is None:
            if title_id is None:
                raise ValueError("IMDb ID must be provided if no detail "
                                 "dictionary is given")
            self.clear()
            self.get_imdb_data(title_id)
        else:
            self.__dict__.update(detail)

    def refresh(self, detail = None):
        """ Update object based on latest IMDb data """
        self.clear()
        if detail is None:
            self.get_imdb_data(self.title_id)
        else:
            self.__dict__.update(detail)

    def get_imdb_data(self, title_id):
        """ Extract data from IMDb for a title id """
        self.title_id = standardise_id(title_id)
        self._title = imdb.get_movie(clean_id(title_id))
        self._data = self._title.data

        self.type = self._data["kind"]

        if self.type == "episode":
            self.series_id = standardise_id(self._data["episode of"].getID())
            self.episode = self._data["episode"]
            self.season = self._data["season"]

        elif self.type == "tv series":
            self.series_id = self.title_id

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
        elif type == "tv series":
            return_dict = self._get_dict(
                ["series_id", "title", "year", "genre", "plot_tag",
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

    def get_tags(self):
        """ Return dictionary of title tags for fields which can take multiple
        values """
        return {
            "director": self._directors,
            "genre": self._genres,
            "writer": self._writers
            }

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
        except Exception as e:
            print(e)
            return
        return release_date

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
    pass

class TitleNotExistsError(base.PolygonException):
    """ Raised when title doesn't exist in database """
    def __init__(self):
        super().__init__("Title does not exist in database")
    pass

class IMDbFunctions:
    def __init__(self):
        self.db = base.polygon_db

    def get_title(self, imdb_id, refresh = True):
        """ Get Title object. Optionally refresh from latest IMDb data."""
        if refresh:
            return Title(title_id = imdb_id)
        else:
            return Title(detail = self.get_detail(imdb_id))

    def get_detail(self, imdb_id):
        """ Return dict of database values for an imdb_id """
        detail = self.db.titles.filter({"imdb_id": imdb_id}, "*")
        return detail

    def add_title(self, imdb_id = None, detail = None):
        """ Insert a title to the database if it does not already exist """
        if imdb_id is None:
            if detail is None:
                raise ValueError("Either IMDb ID or detail dictionary must be"
                                 "provided.")
            imdb_id = detail["imdb_id"]

        if self.title_exists(imdb_id):
            raise TitleExistsError

        if detail is None:
            title = Title(title_id = imdb_id)
        else:
            title = Title(detail = detail)

        title_dict = title.get_dict("title")
        title_dict["import_date"] = self.db.getdate()
        self.db.titles.insert(**title_dict)

    def update_title(self, imdb_id, detail):
        pass

    def title_exists(self, imdb_id):
        """ Return if imdb_id exists in database """
        result = self.db.titles.filter({"title_id": imdb_id}, "title_id")
        return len(result["title_id"]) != 0

    def watch_count(self, imdb_id):
        """ Return watch count for one or more IMDb IDs """
        if not isinstance(imdb_id, list):
            imdb_id = [imdb_id]

imdbf = IMDbFunctions()
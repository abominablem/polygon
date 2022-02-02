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
from mh_logging import log_class
log_class = log_class("None")

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
    @log_class
    def __init__(self, title_id = None, detail = None):
        if not title_id is None:
            self.clear()
            movie = imdb.get_movie(clean_id(title_id))
            self._data_from_object(movie)

        if not detail is None:
            self.__dict__.update(detail)

    @log_class
    def refresh(self, detail = None):
        """ Update object based on latest IMDb data """
        self.clear()
        if detail is None:
            self._data_from_object(imdb.get_movie(clean_id(self.title_id)))
        else:
            self.__dict__.update(detail)

    @log_class
    def from_object(self, movie):
        """ Create Title object from imdb.Movie.Movie object """
        self._data_from_object(movie)

    @log_class
    def _data_from_object(self, movie):
        self.title_id = standardise_id(movie.getID())

        imdb.update(movie, ["akas", "main"])

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
        self.original_title = self._get_original_title(self.year)
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

        rating = self._data_get("rating", None)
        if rating is None:
            self.imdb_user_rating = rating
        else:
            self.imdb_user_rating = round(rating, 1)

        self.imdb_user_votes = self._data_get("votes", 0)

        self.runtime = f.list_default(
            self._data_get("runtimes", []), 0, None
            )

        plot = self._data_get("plot", [])
        if isinstance(plot, str):
            self.plot_tag = plot.strip()
        else:
            self.plot_tag = f.list_default(plot, 0, "").strip()

    @log_class
    def get_episodes(self):
        if not self.type in c.TV_TYPES:
            raise WrongTitleTypeError(self.type)

        if hasattr(self, "_title"):
            imdb.update(self._title, "episodes")

        # Create dictionary of Title object for each season/episode
        self.episodes = {}
        for season in self._data_get("episodes", {}):
            self.episodes[season] = {}
            for episode in self._data["episodes"][season]:
                movie = self._data["episodes"][season][episode]
                title = Title()
                title.from_object(movie)
                self.episodes[season][episode] = title
        return self.episodes

    @log_class
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

    @log_class
    def _data_get(self, key, default):
        """ Get data from imdb.Title.data object """
        return self._data.get(key, default)

    @log_class
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
                ["title_id", "title", "original_title", "type", "year",
                 "genre", "runtime", "plot_tag", "imdb_user_rating",
                 "imdb_user_votes"]
                )
        elif type == "episode":
            return_dict = self._get_dict(
                ["title_id", "series_id", "season", "episode"]
                )
        else:
            raise ValueError("Unrecognised title type")
        return return_dict

    @log_class
    def _get_dict(self, keys):
        return {key: self.__dict__[key] for key in keys}

    @log_class
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

    @log_class
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
        except: #TODO work out exact error if it can't parse
            pass
        return release_date

    @log_class
    def get_series(self):
        """ Return Title object of parent series """
        if self.type == "episode":
            return Title().from_object(self._date["episode of"])
        elif self.type in c.TV_TYPES:
            return self
        else:
            raise WrongTitleTypeError(self.type)

    @log_class
    def _clean_original_title(self, original_title, year):
        """ Remove ' (XXXX)' from the end of the title where XXXX is the
        release year """
        if year is None:
            return original_title
        elif original_title[-7:] == " (%s)" % year:
            return original_title[:-7]
        elif original_title[-17:] == " (original title)":
            return original_title[:-17]
        else:
            return original_title

    def _get_original_title(self, year):
        """ Get the original title, based on the akas and release year """
        akas = self._data_get("akas", [])
        original_title = (self._data_get("original title", self.title)
                          if akas == [] or len(akas) == 0 else akas[0])
        return self._clean_original_title(original_title, year)

    @log_class
    def _get_names(self, people, firstn = 0):
        if not isinstance(people, list):
            people = [people]

        if firstn > 0:
            people = people[:firstn]

        names = [person.data['name'] for person in people]
        return names

    @log_class
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
    @log_class
    def __init__(self):
        self.titles = IMDbTitleFunctions()
        self.entries = IMDbEntryFunctions()
        self.entry_tags = IMDbEntryTagsFunctions()
        self.title_tags = IMDbTitleTagsFunctions()
        self.series = IMDbSeriesFunctions()
        self.episodes = IMDbEpisodesFunctions()
        self.db = base.polygon_db

    @log_class
    def exists(self, title):
        if isinstance(title, Title):
            title_id = title.title_id
        elif isinstance(title, str):
            title_id = title
        elif isinstance(title, dict):
            title_id = title["title_id"]
        else:
            raise ValueError("Unknown input type %s" % type(title))

        return self.titles.exists(title_id)

    @log_class
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

    @log_class
    def _add_episode(self, title):
        """ Test adding an episode and raise any errors that would occur. These
        are then handled in the front end by either importing or updating the
        series data """
        # check if the parent series exists in database
        if not self.series.exists(title.series_id):
            raise SeriesNotExistsError

        # check if the episode exists as a title in the database
        if self.titles.exists(title):
            raise EpisodeExistsError

        self.episodes.add(title)

    @log_class
    def _add_series(self, title):
        """ Add a new series to the series table and add the episodes """
        try:
            self.series.add(title)
        except TitleExistsError:
            pass
        self.episodes.add(title)
        self.title_tags.add_dict(title.title_id, title.get_tags("series"))

    @log_class
    def _add_title(self, title):
        self.titles.add(title)
        self.title_tags.add_dict(title.title_id, title.get_tags("title"))

    @log_class
    def add_entry(self, title_id, tags = None, **kwargs):
        """ Add new entry to the entries table. """
        try:
            self.add_title(title_id)
        except TitleExistsError:
            pass
        self.entries.add(title_id, **kwargs)
        # get the auto-generated id of the entry that was just added
        filters = kwargs
        try: del filters["rewatch"]
        except KeyError: pass
        entry_id = max(self.entries.get_entry_id(title_id = title_id, **filters))
        self.entry_tags.add_dict(entry_id, tags)

    def get_entry_by_rank(self, rank = None, type = None, rewatch = None):
        """ Return a dictionary of values for use in a TitleModule widget
        based on the provided single or iterable of entry ranks """
        # filter to apply to the inner joined entries/titles table
        inner_filters = [" entry_date IS NOT NULL"]
        if type is None:
            pass
        elif type == "movie":
            inner_filters.append("type IN ('%s')" % "', '".join(c.MOVIE_TYPES))
        else:
            raise ValueError("Invalid type")

        if rewatch is None or rewatch:
            pass
        elif not rewatch:
            inner_filters.append("rewatch = 'False'")

        if inner_filters == []:
            where = ""
        else:
            where = "WHERE " + " AND ".join(inner_filters)

        all_ranks = (rank is None)

        if all_ranks:
            rank = ""
        else:
            if isinstance(rank, str) or isinstance(rank, int):
                rank = [rank]
            rank_int = [int(rk) for rk in rank]
            rank_int.sort()
            rank_str = [str(rk) for rk in rank_int]
            rank = "WHERE rank IN (%s)" % ",".join(rank_str)

        query = """
        SELECT [date], title, original_title, director, year, runtime, rating,
        rewatch
        FROM (
            SELECT e.entry_date as [date], COALESCE(t.custom_title, t.title)
            AS title, t.original_title, t.director, t.year, t.runtime, e.rating,
            e.rewatch,
            RANK() OVER(ORDER BY [entry_date] DESC, entry_order DESC) AS [rank]
            FROM
            entries e
            LEFT JOIN
            titles t
            ON e.title_id = t.title_id
            %s
            )
        %s
        """ % (where, rank)

        result = self.db.entries.select(query)
        cols = ["date", "title", "original_title", "director", "year",
                "runtime", "rating", "rewatch"]
        if all_ranks: rank_int = range(1, len(result) + 1)
        results_dict_all = {}
        for index, rank in enumerate(rank_int):
            result_tuple = result[index]
            result_dict = {cols[i]: val for i, val in enumerate(result_tuple)}
            result_dict["rewatch"] = (result_dict["rewatch"] == "True")
            result_dict["number"] = rank
            results_dict_all[rank] = result_dict
        return results_dict_all

    def _search_object_to_dict(self, search_obj):
        obj_dict = {
            key: search_obj.data.get(key, "") for key in
            ["title", "kind", "year", "episode of", "series year", "season",
             "episode"]
            }
        obj_dict["title_id"] = search_obj.getID()
        obj_dict["type"] = obj_dict["kind"]
        return obj_dict

    def search_title(self, search_text, type = None):
        """ Return search results for some search_text. Optionally filter by
        title type """
        search_results = imdb.search_movie(search_text)
        if not type is None:
            try:
                type_filter = {"movie": c.MOVIE_TYPES, "tv": c.TV_TYPES,
                               "episode": ["episode"]}[type]
            except KeyError:
                if not isinstance(type, list): type_filter = [type]

            results_filtered = [movie for movie in search_results
                                if movie.data["kind"] in type_filter]
        else:
            results_filtered = search_results
        return [self._search_object_to_dict(movie)
                for movie in results_filtered]


class IMDbBaseTitleFunctions:
    """ Base class for function classes editing the titles table """
    def __init__(self):
        pass

    @log_class
    def exists(self, title):
        """ Return if series exists in database """
        if isinstance(title, Title):
            title = title.title_id
        return self.exists_id(title)

    @log_class
    def exists_id(self, title_id):
        """ Return if title_id exists in database """
        result = self.db.filter({"title_id": title_id}, "title_id")
        return len(result["title_id"]) != 0

    @log_class
    def update(self, imdb_id, detail):
        #TODO
        pass

    @log_class
    def get_detail(self, imdb_id):
        """ Return dict of database values for an imdb_id """
        if not self.exists(imdb_id):
            raise TitleNotExistsError
        detail = self.db.filter({"title_id": imdb_id}, "*", rc = "rowdict")[0]
        return detail

    @log_class
    def get(self, imdb_id, refresh = False):
        """ Get Title object. Optionally refresh from latest IMDb data."""
        if refresh:
            return Title(title_id = imdb_id)
        else:
            try:
                return Title(detail = self.get_detail(imdb_id))
            except TitleNotExistsError:
                return Title(title_id = imdb_id)


class IMDbEpisodesFunctions(IMDbBaseTitleFunctions):
    """ Container for functions relating to the episodes table """
    @log_class
    def __init__(self):
        super().__init__()
        self.episodes_db = base.polygon_db.episodes
        self.db = base.polygon_db.titles

    @log_class
    def add(self, title):
        """ Add an episode or series of episodes to the database """
        if title.type in c.TV_TYPES:
            self._add_series_episodes(title)
        elif title.type == "episode":
            if self.exists(title):
                return
            self._add_episode(title)
        else:
            raise WrongTitleTypeError(title.type)

    @log_class
    def _add_episode(self, title):
        """ Add an episode to the titles table """
        title_dict = title.get_dict("title")
        title_dict["import_date"] = self.db.getdate()
        self.db.insert(**title_dict)
        self.episodes_db.insert(**title.get_dict("episode"))

    @log_class
    def _add_series_episodes(self, title):
        """ Add all episodes in series to database """
        series = title.get_episodes()
        for season in series:
            for episode in series[season]:
                title = Title(series[season][episode].title_id)
                self.add(title)

class IMDbSeriesFunctions(IMDbBaseTitleFunctions):
    """ Container for functions relating to the series table """
    @log_class
    def __init__(self):
        super().__init__()
        self.db = base.polygon_db.titles
        self.series_db = base.polygon_db.series

    @log_class
    def add(self, title):
        """ Insert a series to the database if it does not already exist """
        if not title.type in c.TV_TYPES:
            raise WrongTitleTypeError(title_type = title.type)

        if self.exists(title):
            raise SeriesExistsError

        title_dict = title.get_dict("series")
        title_dict["import_date"] = self.db.getdate()
        self.db.insert(**title_dict)
        self.series_db.insert(series_id = title.title_id)
        return title

class IMDbTitleTagsFunctions:
    """ Container for functions relating to the entry_tags table """
    @log_class
    def __init__(self):
        self.db = base.polygon_db.title_tags

    @log_class
    def add_dict(self, title_id, tag_dict):
        for tag_name, tags in tag_dict.items():
            if not isinstance(tags, list):
                tags = [tags]
            for tag_value in tags:
                self.add(title_id, tag_value, tag_name)

    @log_class
    def add(self, title_id, tag_value, tag_name = None):
        # tags should never be duplicated
        if self.exists(title_id, tag_value, tag_name):
            # raise TagExistsError
            return

        detail = dict(title_id = title_id, tag_value = tag_value)
        if not tag_name is None:
            detail["tag_name"] = tag_name

        self.db.insert(**detail)

    @log_class
    def exists(self, title_id, tag_value, tag_name = None):
        result = self.db.filter({"title_id": title_id,
                                 "tag_value": tag_value,
                                 "tag_name": tag_name}, "title_id")
        return len(result["title_id"]) != 0

class IMDbEntryTagsFunctions:
    """ Container for functions relating to the entry_tags table """
    @log_class
    def __init__(self):
        self.db = base.polygon_db.entry_tags

    @log_class
    def add_dict(self,entry_id, tag_dict):
        for tag_name, tags in tag_dict.items():
            if not isinstance(tags, list):
                tags = [tags]
            for tag_value in tags:
                self.add(entry_id, tag_value, tag_name)

    @log_class
    def add(self, entry_id, tag_value, tag_name = None):
        if self.exists(entry_id, tag_value, tag_name):
            raise TagExistsError

        detail = dict(entry_id = entry_id, tag_value = tag_value)
        if not tag_name is None:
            detail["tag_name"] = tag_name

        self.db.insert(**detail)

    @log_class
    def exists(self, entry_id, tag_value, tag_name = None):
        result = self.db.filter({"entry_id": entry_id,
                                 "tag_value": tag_value,
                                 "tag_name": tag_name}, "entry_id")
        return len(result["entry_id"]) != 0

class IMDbTitleFunctions(IMDbBaseTitleFunctions):
    """ Container for functions relating to the Titles table """
    @log_class
    def __init__(self):
        super().__init__()
        self.db = base.polygon_db.titles

    @log_class
    def add(self, title):
        """ Insert a title to the database if it does not already exist """
        if title.type in c.TV_TYPES:
            raise WrongTitleTypeError(title_type = title.type)

        title_dict = title.get_dict("title")
        title_dict["import_date"] = self.db.getdate()
        self.db.insert(**title_dict)
        return title

class IMDbEntryFunctions:
    """ Container for functions relating to the Entries table """
    @log_class
    def __init__(self):
        self.db = base.polygon_db.entries

    @log_class
    def add(self, title_id, entry_date = None, entry_order = None,
            rating = None, rewatch = False):
        """ Insert a new entry row into entries table """
        if isinstance(title_id, Title):
            title_id = title_id.title_id
        detail = dict(
            title_id = title_id,
            rewatch = rewatch
            )

        if not entry_date is None:
            detail["entry_date"] = entry_date

        # if the entry order is not specified, assume entries were logged
        # chronologically and add one to the maximum order
        if entry_date is None:
            pass
        elif entry_order is None:
            detail["entry_order"] = self._get_entry_order(entry_date)
        else:
            self._offset_entries(entry_date, entry_order)
            detail["entry_order"] = entry_order

        if not rating is None: detail["rating"] = rating

        self.db.insert(**detail)

    @log_class
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

    @log_class
    def _get_entry_order(self, entry_date):
        """ Get the next order number for an entry_date """
        rows = self.db.select("SELECT COUNT(*) FROM entries "
                              "WHERE entry_date = '%s'" % entry_date)
        return rows[0][0] + 1

    @log_class
    def get_entry_id(self, **kwargs):
        result = self.db.filter(kwargs, "entry_id")
        return result["entry_id"]


imdbf = IMDbFunctions()
# # imdbf.add_entry(title_id = 'tt13984924', entry_date = '2022-01-31', rating = 7, rewatch = False, tags  = {'platform': 'Download'})
# base.polygon_db.close()
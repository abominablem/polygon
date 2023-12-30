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
log_class = log_class(c.LOG_LEVEL)

imdb = IMDb()

def clean_id(title_id):
    """ Remove all non-numeric characters from the id, including
    leading "tt" """
    return re.sub("[^\d]", "", title_id)

def standardise_id(title_id):
    """ Standardise the given id with leading "tt" """
    title_id = str(title_id)
    if title_id[0:2] != "tt":
        return "tt" + title_id
    else:
        return title_id

class Title:
    @log_class
    def __init__(self, title_id = None, detail = None, get_episodes = False):
        self._get_episodes = get_episodes
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
    def from_object(self, movie, update = True):
        """ Create Title object from imdb.Movie.Movie object """
        self._data_from_object(movie, update = update)

    @log_class
    def _data_from_object(self, movie, update = True):
        self.title_id = standardise_id(movie.getID())

        if update:
            imdb.update(movie, ["akas", "main"])

        self._title = movie
        self._data = self._title.data

        self.type = self._data.get("kind", "movie")

        if self.type in c.EPISODE_TYPES:
            self.series_id = standardise_id(self._data["episode of"].getID())
            self.episode = self._data["episode"]
            self.season = self._data["season"]

        elif self.type in c.TV_TYPES:
            self.series_id = self.title_id
            if self._get_episodes:
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
    def get_episodes(self, basic_only = False):
        if not self.type in c.TV_TYPES:
            raise WrongTitleTypeError(self.type)

        try:
            self.update("episodes")
        except AttributeError:
            pass

        # Create dictionary of Title object for each season/episode
        self.episodes = {}
        for season in self._data_get("episodes", {}):
            self.episodes[season] = {}
            for episode in self._data["episodes"][season]:
                movie = self._data["episodes"][season][episode]
                title = Title()
                title.from_object(movie, update = not basic_only)
                self.episodes[season][episode] = title
        return self.episodes

    @log_class
    def update(self, type):
        if hasattr(self, "_title"):
            imdb.update(self._title, type)
        else:
            raise AttributeError("Title has no _title imdb.Movie attribute")

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

    def _get_type(self):
        if self.type in c.MOVIE_TYPES:
            return 'title'
        elif self.type in c.TV_TYPES:
            return 'series'
        elif self.type in c.EPISODE_TYPES:
            return 'episode'
        else:
            return None

    @log_class
    def get_dict(self, type = None):
        """ Get dictionary of values used in a given table """
        if type is None:
            type = self._get_type()
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
    def get_tags(self, type = None):
        """ Return dictionary of title tags for fields which can take multiple
        values """
        if type is None:
            type = self._get_type()
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
    def get_series(self, get_episodes = False):
        """ Return Title object of parent series """
        if self.type == "episode":
            return Title(get_episodes = get_episodes).from_object(self._data["episode of"])
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

    @log_class
    def _get_original_title(self, year):
        """ Get the original title, based on the akas and release year """
        akas = self._data_get("akas", [])
        # list of potential titles, is order of priority
        # fall back to the default title if no other titles available
        titles = [
            self._data_get("original title", None),
            self._data_get("localized title", None),
            None if akas == [] or len(akas) == 0 else akas[0],
            self.title
            ]
        # take the first non-None value
        original_title = next(
            (title for title in titles if title is not None),
            None
            )
        return self._clean_original_title(original_title, year)

    @log_class
    def _get_names(self, people, firstn = 0):
        if not isinstance(people, list):
            people = [people]

        if firstn > 0:
            people = people[:firstn]

        names = [person.data['name'] for person in people
                 if person.data.get('name', None) is not None]
        return names

    def __str__(self):
        try:
            if self.type == "episode":
                date = "??" if self.release_date is None else self.release_date
                season = "??" if self.season == 'unknown' else self.season
                episode = "??" if self.episode == 'unknown' else self.episode
                return "<%s : %s : %s S%sE%s %s (%s)>" % (
                    self.title_id, self.type,
                    self._data["episode of"].get("title"), season, episode,
                    self.title, date
                    )
            elif self.type == "series":
                return "<%s : %s : %s (%s)>" % (
                    self.title_id, self.type, self.title,
                    self._data_get("series years", "??")
                    )
            else:
                year = "??" if self.year is None else self.year
                return "<%s : %s : %s (%s)>" % (
                    self.title_id, self.type, self.title, year
                    )
        except AttributeError:
            if self.type == "episode":
                date = "??" if self.release_date is None else self.release_date
                return "<%s : %s : %s S%sE%s %s (%s)>" % (
                    self.title_id, self.type, "<unknown>", "??",
                    "??", self.title, date
                    )
            elif self.type == "series":
                return "<%s : %s : %s (%s)>" % (
                    self.title_id, self.type, self.title,
                    self._data_get("series years", "??")
                    )
            else:
                year = "??" if self.year is None else self.year
                return "<%s : %s : %s (%s)>" % (
                    self.title_id, self.type, self.title, year
                    )

    __repr__ = __str__

    def __getitem__(self, arg):
        return self.__dict__[arg]

class TitleExistsError(base.PolygonException):
    """ Raised when title already exists in database """
    def __init__(self, text = "Title already exists in database"):
        super().__init__(text)

class TitleNotExistsError(base.PolygonException):
    """ Raised when title doesn't exist in database """
    def __init__(self, text = "Title does not exist in database"):
        super().__init__(text)

class SeriesExistsError(base.PolygonException):
    """ Raised when series already exists in database """
    def __init__(self, text = "Series already exists in database"):
        super().__init__(text)

class SeriesNotExistsError(base.PolygonException):
    """ Raised when series doesn't exist in database """
    def __init__(self, text = "Series does not exist in database"):
        super().__init__(text)

class EpisodeExistsError(base.PolygonException):
    """ Raised when episode already exists in database """
    def __init__(self, text = "Episode already exists in database"):
        super().__init__(text)

class EpisodeNotExistsError(base.PolygonException):
    """ Raised when episode doesn't exist in database """
    def __init__(self, text = "Episode does not exist in database"):
        super().__init__(text)

class EntryExistsError(base.PolygonException):
    """ Raised when an entry exists in the database when it shouldn't """
    def __init__(self, text = "Entry exists in the database"):
        super().__init__(text)

class TagExistsError(base.PolygonException):
    """ Raised when tag combination already exists in database """
    def __init__(self, text = "Tag already exists in database"):
        super().__init__(text)

class WrongTitleTypeError(base.PolygonException):
    """ Raised when the given title has the wrong title type for the attempted
    operation """
    def __init__(self, text = "Invalid title type for this operation",
                 title_type = None):
        super().__init__(text)
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
        self.watchlist = IMDbWatchlistFunctions()
        self.db = base.polygon_db

    @log_class
    def get_title_id(self, title):
        if isinstance(title, Title):
            title_id = title.title_id
        elif isinstance(title, str):
            title_id = title
        elif isinstance(title, dict):
            title_id = title["title_id"]
        else:
            raise ValueError("Unknown input type %s" % type(title))
        return title_id

    @log_class
    def _get_title(self, title):
        if isinstance(title, Title):
            pass
        elif isinstance(title, str):
            title = Title(title)
        elif isinstance(title, dict):
            title = Title(detail = title)
        else:
            raise ValueError("Unknown input type %s" % type(title))
        return title

    @log_class
    def exists(self, title):
        """ Test if a given title exists in the database. Supports Title
        object, title_id string, or dictionary containing title_id """
        title_id = self.get_title_id(title)
        return self.titles.exists(title_id)

    @log_class
    def add_title(self, title):
        """ Add a new title/series to the correct table """
        if self.exists(title):
            if self.title_is_unreleased(title):
                self.update_title(title)
            return

        title = self._get_title(title)

        try:
            if title.type in c.TV_TYPES:
                self._add_series(title)
            elif title.type in c.EPISODE_TYPES:
                self._add_episode(title)
            else:
                self._add_title(title)
        except TitleExistsError:
            raise

    @log_class
    def update_title(self, title):
        """ Update existing title with the latest data from IMDb, or a
        given dictionary/Title of data """
        if isinstance(title, str):
            title = self.get_title(title, refresh = True, get_episodes = False)
        elif isinstance(title, Title):
            pass
        elif isinstance(title, dict):
            title = Title(detail = title)

        title_dict = title.get_dict('title')
        self.titles.update(**title_dict)

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
        # if previous entry already exists for the title, set rewatch to True
        # unless explicitly specified
        if self.entries.exists(title_id = title_id):
            kwargs.setdefault("rewatch", True)
        self.entries.add(title_id, **kwargs)
        # get the auto-generated id of the entry that was just added
        filters = kwargs
        try: del filters["rewatch"]
        except KeyError: pass
        entry_id = max(self.entries.get_entry_id(title_id = title_id, **filters))
        self.entry_tags.add_dict(entry_id, tags)

    @log_class
    def add_to_watchlist(self, title_id, add_title = True, **kwargs):
        """ Add a title to the watchlist, and optionally add it to the titles
        table as well """
        if add_title:
            self.add_title(title_id)
        # raise an error if the title has already been watched
        elif self.entries.exists(title_id = title_id):
            raise EntryExistsError
        self.watchlist.add(title_id, **kwargs)

    @log_class
    def get_entry_by_rank(self, rank = None, type = None, rewatch = None):
        """ Return a dictionary of values for use in a TitleModule widget
        based on the provided single or iterable of entry ranks """
        # filter to apply to the inner joined entries/titles table
        inner_filters = [" e.entry_date IS NOT NULL"]
        if type is None:
            pass
        elif type == "movie":
            inner_filters.append("t.type IN ('%s')" % "', '".join(c.MOVIE_TYPES))
            inner_filters.append("t.runtime >= 45")
            inner_filters.append("t.title_id NOT LIKE 'cc%'") # exclude custom titles
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
            RANK() OVER(ORDER BY entry_date DESC, entry_order DESC) AS [rank]
            FROM entries e LEFT JOIN titles t
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

    @log_class
    def _search_object_to_dict(self, search_obj):
        obj_dict = {
            key: search_obj.data.get(key, "") for key in
            ["title", "kind", "year", "episode of", "series year", "season",
             "episode"]
            }
        obj_dict["title_id"] = search_obj.getID()
        obj_dict["type"] = obj_dict["kind"]
        return obj_dict

    @log_class
    def search_title(self, search_text, type = None):
        """ Return search results for some search_text. Optionally filter by
        title type """
        search_results = imdb.search_movie(search_text)
        if not type is None:
            try:
                type_filter = {"movie": c.MOVIE_TYPES,
                               "tv": c.TV_TYPES,
                               "episode": c.EPISODE_TYPES}[type]
            except KeyError:
                if not isinstance(type, list): type_filter = [type]

            results_filtered = [movie for movie in search_results
                                if movie.data["kind"] in type_filter]
        else:
            results_filtered = search_results
        return [self._search_object_to_dict(movie)
                for movie in results_filtered]

    @log_class
    def get_title(self, title_id, refresh = False, get_episodes = False):
        """ Get Title object for an id """
        title = self.titles.get(title_id, refresh, get_episodes)
        if title.type in c.EPISODE_TYPES:
            if not hasattr(title, 'series_id'):
                title.series_id = self.episodes.get_series_id(title_id)
            title.series = self.titles.get(title.series_id, refresh)
        return title

    @log_class
    def get_tags(self, title_id):
        return self.title_tags.get_dict(title_id)

    @log_class
    def get_series_with_entries(self, title_id, refresh):
        """ Get Title object for a series, with an Entry object for each
        episode """
        series = self.get_series(title_id, refresh = refresh, get_episodes = True)
        for episode in series.episodes:
            episode.entry = Entry(episode.title_id)
        return series

    @log_class
    def get_series(self, title_id, refresh = False, get_episodes = True):
        series = self.get_title(title_id, refresh = refresh)
        if get_episodes:
            series.episodes = self.get_episodes(title_id, refresh)
            seasons = {episode.season for episode in series.episodes}
            series.seasons = {season: [] for season in seasons}
            for episode in series.episodes:
                series.seasons[episode.season].append(episode)
        return series

    @log_class
    def get_episodes(self, title_id, refresh = False):
        episode_dict = self.episodes.get_ids(title_id)
        titles = []
        for episode in episode_dict:
            title = self.get_title(episode["title_id"], refresh)
            title.__dict__.update(episode)
            titles.append(title)
        return titles

    @log_class
    def get_entry(self, title_id):
        return Entry(title_id)

    @log_class
    def get_all_title_tags(self):
        results = base.polygon_db.title_tags.select(
            "SELECT title_id, tag_name, tag_value FROM title_tags")
        tags_dict = {}
        for row in results:
            title_id, tag_name, tag_value = row
            tags_dict.setdefault(title_id, {})
            tags_dict[title_id].setdefault(tag_name, [])
            tags_dict[title_id][tag_name].append(tag_value)
        return tags_dict


    @log_class
    def get_watchlist(self, filters = None):
        """ Get data for all titles on the watchlist not yet watched, including
        title tags """
        db = base.polygon_db.watchlist
        if filters is None:
            where = "WHERE e.title_id IS NULL"
        else:
            where = "(%s) AND e.title_id IS NULL" % db._get_where(filters)

        query = """
            SELECT w.title_id, t.title, t.original_title, t.director,
                t.year, t.runtime, t.imdb_user_rating, t.plot_tag, w.log_date
            FROM watchlist w
            LEFT JOIN titles t
            ON w.title_id = t.title_id
            LEFT JOIN entries e
            ON w.title_id = e.title_id
            %s
            ORDER BY w.log_date, t.title
            """ % where
        results = db.select(query)
        cols = ["title_id", "title", "original_title", "director", "year",
                "runtime", "rating", "plot_tag", "date"]
        tags_dict = self.get_all_title_tags()
        results_dict = {}
        for index, row in enumerate(results):
            row_dict = {cols[i]: val for i, val in enumerate(row)}
            row_dict["number"] = index
            row_dict["tags"] = tags_dict[row_dict["title_id"]]
            results_dict[index] = row_dict
        return results_dict

    @log_class
    def title_is_unreleased(self, title_id):
        """ Check based on data currently in database if the title was added
        before it was released """
        if not self.exists(title_id):
            raise TitleNotExistsError

        td = base.polygon_db.titles.filter(
            {'title_id': title_id}, return_cols = "*", rc = 'rowdict'
                       )[0]

        if (td['imdb_user_rating'] == 'None' or
            td['year'] == 'None' or
            str(td['year']) > td['import_date'][:4] or
            td['title'][-7:] == ' - IMDb'):
            return True

        elif td['type'] in c.EPISODE_TYPES:
            if (td['release_date'] == 'None'):
                return True

        return False


class IMDbBaseTitleFunctions:
    """ Base class for function classes editing the titles table """
    def __init__(self):
        pass

    @log_class
    def exists(self, title):
        """ Return if title exists in database """
        if isinstance(title, Title):
            title = title.title_id
        return self.exists_id(title)

    @log_class
    def exists_id(self, title_id):
        """ Return if title_id exists in database """
        title_id = standardise_id(title_id)
        result = self.db.filter({"title_id": title_id}, "title_id")
        return len(result["title_id"]) != 0

    @log_class
    def update(self, title_id, **kwargs):
        """ Update data for a given title_id """
        if not self.exists(title_id):
            raise TitleNotExistsError
        kwargs['update_date'] = self.db.getdate()
        self.db.update(filters = {'title_id': title_id}, **kwargs)

    @log_class
    def get_detail(self, title_id):
        """ Return dict of database values for an title_id """
        if not self.exists(title_id):
            raise TitleNotExistsError
        detail = self.db.filter({"title_id": title_id}, "*", rc = "rowdict")[0]
        return detail

    @log_class
    def get(self, title_id, refresh = False, get_episodes = False):
        """ Get Title object. Optionally refresh from latest IMDb data."""
        if refresh:
            return Title(title_id = title_id, get_episodes = get_episodes)
        else:
            try:
                return Title(detail = self.get_detail(title_id))
            except TitleNotExistsError:
                return Title(title_id = title_id)



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
        elif title.type in c.EPISODE_TYPES:
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
        title_dict['update_date'] = title_dict["import_date"]
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

    @log_class
    def get_ids(self, series_id):
        """ Get all episode ids along with seasons and episode numbers for a
        given series """
        detail = self.episodes_db.filter(
            filters = {"series_id": series_id}, return_cols = "*",
            rc = "rowdict"
            )
        return detail

    @log_class
    def get_series_id(self, title_id):
        """ Get the corresponding series_id for an episode title_id """
        detail = self.episodes_db.filter(
            filters = {"title_id": title_id}, return_cols = "series_id",
            rc = "columns"
            )["series_id"][0]
        return detail


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
        title_dict['update_date'] = title_dict["import_date"]
        self.db.insert(**title_dict)
        self.series_db.insert(series_id = title.title_id)
        return title

    @log_class
    def get(self, *args, **kwargs):
        raise NotImplementedError


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
    def get_dict(self, title_id):
        tags = self.db.filter(
            filters = {"title_id": title_id},
            return_cols = ["tag_name", "tag_value"], rc = "columns"
            )
        names = tags["tag_name"]
        values = tags["tag_value"]
        tag_dict = {}

        for i, name in enumerate(names):
            tag_dict.setdefault(name, [])
            tag_dict[name].append(values[i])

        return tag_dict

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
    def add_dict(self, entry_id, tag_dict):
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
        title_dict['update_date'] = title_dict["import_date"]
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
        """ Get all columns for a given entry_id """
        result = self.db.filter(kwargs, "entry_id")
        return result["entry_id"]

    @log_class
    def exists(self, **kwargs):
        """ Test if entry exists for a given set of arguments """
        result = self.db.filter(kwargs, "title_id")
        return len(result["title_id"]) != 0


class Entry:
    def __init__(self, title_id):
        self.entries = base.polygon_db.entries.filter(
            filters = {"title_id": title_id}, return_cols = "*",
            rc = "rowdict"
            )
        self.watched = (len(self.entries) > 0)
        self.first = {"entry_id": None, "entry_date": None,
                      "entry_order": None, "rating": None, "rewatch": None}
        for entry in self.entries:
            if entry["rewatch"] == 'False':
                self.first = entry
                break

        self.id = self.first["entry_id"]
        self.date = self.first["entry_date"]
        self.order = self.first["entry_order"]
        self.rating = self.first["rating"]
        self.rewatch = self.first["rewatch"] == 'True'
        self.title_id = title_id

    def __int__(self):
        return self.id

    def __str__(self):
        return "<#%s %s %s~%s>" % (self.id, self.title_id, self.date, self.order)

    __repr__ = __str__


class IMDbWatchlistFunctions(IMDbBaseTitleFunctions):
    """ Container for functions relating to the Watchlist table """
    @log_class
    def __init__(self):
        super().__init__()
        self.db = base.polygon_db.watchlist
        self.titles_db = base.polygon_db.titles

    @log_class
    def add(self, title_id, **kwargs):
        """ Insert a title to the database if it does not already exist """
        title_id = standardise_id(title_id)
        if self.exists(title_id):
            raise TitleExistsError("Title is already on the watchlist")
        self.db.insert(title_id = title_id, **kwargs)

    @log_class
    def get(self, *args, **kwargs):
        raise NotImplementedError

imdbf = IMDbFunctions()

if __name__ == "__main__":
    pass
    # imdbf.add_to_watchlist('tt21113540')
    title = imdbf.get_title("tt4643084", refresh = True, get_episodes = True)    imdbf.add_to_watchlist('tt1865505')

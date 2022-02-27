# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 20:40:22 2022

@author: marcu
"""
import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import random

from mh_logging import log_class
import tk_arrange as tka
import described_widgets as dw
import constants as c
import base
import futil
from imdb_functions import imdbf
import imdb_functions
from widgets import (RequestTitleWindow, PolygonButton, OptionList,
                     PolygonProgressBar)
from log_entry import LogEntryWindow

log_class = log_class(c.LOG_LEVEL)

class RequestTVWindow:
    @log_class
    def __init__(self):
        pass

class SeasonCounter(tk.Frame):
    @log_class
    def __init__(self, master, minimum = 1, maximum = None, *args, **kwargs):
        self.minimum = minimum
        self.maximum = 9223372036854775807 if maximum is None else maximum
        self.season = 1

        super().__init__(master, *args, **kwargs)
        self.counter_frame = base.TrimmedFrame(self, bg = c.COLOUR_TV_BACKGROUND)
        self.counter_frame.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.counter_frame.columnconfigure(0, weight = 1)
        self.counter_frame.rowconfigure(0, weight = 1)

        self._pixel = tk.PhotoImage(width = 1, height = 1)
        self.font_count_size = 30
        self.font_count = ("Calibri", self.font_count_size)

        self.counter = tk.Label(
            self.counter_frame.inner, text = "Season 1",
            font = self.font_count, padx = 25, image = self._pixel,
            compound = "center", anchor = "center", width = 250
            )

        self.counter.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

    @log_class
    def set(self, count, suppress_event = False):
        count = self.enforce_bounds(count)
        self.season = int(count)
        self.counter.config(text = "Season %s" % count)
        if not suppress_event:
            self.event_generate("<<SeasonChange>>")

    @log_class
    def get(self, *args, **kwargs):
        return self.season

    @log_class
    def set_maximum(self, maximum):
        self.maximum = maximum
        if self.season > maximum:
            self.increment(maximum - self.season)

    @log_class
    def set_minimum(self, minimum):
        self.minimum = minimum
        if self.season < minimum:
            self.increment(self.season - minimum)

    @log_class
    def enforce_bounds(self, value):
        return max(self.minimum, min(self.maximum, value))

    @log_class
    def increment(self, *args, loop = True, **kwargs):
        cur_val = self.get()
        if cur_val + 1 > self.maximum and loop:
            self.set(self.minimum)
        else:
            self.set(cur_val + 1)
        self.event_generate("<<SeasonChange>>")

    @log_class
    def decrement(self, *args, loop = True, **kwargs):
        cur_val = self.get()
        if cur_val - 1 < self.minimum and loop:
            self.set(self.maximum)
        else:
            self.set(cur_val - 1)
        self.event_generate("<<SeasonChange>>")

class CompletionTracker(base.TrimmedFrame):
    @log_class
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        columns = {
            1: {"header": "", "width": 1,
                "stretch": False, "anchor": "center"},
            2: {"header": "Season", "width": 110,
                "stretch": True, "anchor": "center"},
            3: {"header": "#", "width": 40,
                "stretch": True, "anchor": "center"},
            4: {"header": "%", "width": 80,
                "stretch": True, "anchor": "center"},
            }
        self.table = dw.SimpleTreeview(
            self.inner, columns, style = "EpisodeTable.Treeview", edit = False
            )
        self.table.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

    @log_class
    def update(self, series):
        self.table.clear()
        for number, season in series.seasons.items():
            self.table.insert(
                "", "end", iid = number, text = "", values = (
                    number,
                    len(season),
                    self.get_season_completion(season, "percentage")
                    )
                )

    @log_class
    def get_season_completion(self, season, type = "percentage"):
        ep_count = len(season)
        watch_count = len([episode for episode in season
                           if episode.entry.watched])
        if type == "percentage":
            completion = watch_count / ep_count
            return str(int(completion*100)) + "%"
        elif type == "ratio":
            return f"{watch_count}/{ep_count}"
        else:
            raise ValueError("Invalid completion type")

class WatchEntry:
    @log_class
    def __init__(self, date = None, rating = None):
        self.date = date
        self.rating = rating
        self.watched = not date is None
        self.watched_string = "Yes" if self.watched else "No"

class EpisodeTable(base.TrimmedFrame):
    @log_class
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        columns = {
            1: {"header": "#", "width": 70,
                "stretch": False, "anchor": "center"},
            2: {"header": "Episode name", "width": 600,
                "stretch": True, "anchor": "w"},
            3: {"header": "Watched?", "width": 200,
                "stretch": False, "anchor": "center"},
            4: {"header": "Date watched", "width": 220,
                "stretch": False, "anchor": "center"},
            5: {"header": "Rating", "width": 150,
                "stretch": False, "anchor": "center"},
            6: {"header": "Runtime", "width": 150,
                "stretch": False, "anchor": "center"},
            }
        self.table = dw.SimpleTreeview(
            self.inner, columns, style = "EpisodeTable.Treeview",
            edit = {"focus_lost_confirm": True, "font": ('Calibri', 20),
                    "event": "<1>", 'columns': ['Episode name']},
            )
        self.table.grid(row = 0, column = 0, **c.GRID_STICKY)

        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

    @log_class
    def border_frame(self, master, **kwargs):
        return tk.Frame(
            master, **kwargs, highlightthickness = 1,
            highlightbackground = self.inner_colour,
            highlightcolor = self.inner_colour
            )

    @log_class
    def add_episodes(self, titles):
        if not isinstance(titles, list):
            titles = [titles]

        children = self.table.get_children()
        for i, title in enumerate(titles):
            values = self.get_values(title)
            if title.title_id in children:
                continue
            self.table.insert("", index = "end", iid = title.title_id,
                              text = title.episode, values = values)
    @log_class
    def get_values(self, title):
        if title.entry.watched:
            date = ("" if title.entry.date is None
                    else datetime.strptime(
                        title.entry.date, "%Y-%m-%d").strftime("%d/%m/%Y"))
            rating = "" if title.entry.rating is None else title.entry.rating
            return (title.title, "Yes", date, rating, title.runtime)
        else:
            return (title.title, "No", "", "", title.runtime)

    @log_class
    def clear(self):
        self.table.clear()

class TvTracker(tk.Frame):
    @log_class
    def __init__(self, master, *args, **kwargs):
        self._during_startup = True
        super().__init__(master, *args, **kwargs)
        self.window = futil.get_tk(self)

        """ Build header with buttons and summary """
        self._pixel = tk.PhotoImage(width = 1, height = 1)
        self.widget_frame = tk.Frame(self, bg = c.COLOUR_TV_BACKGROUND)
        self.show_title_frame = base.TrimmedFrame(self.widget_frame, height = 100)
        self.show_title = tk.Label(
            self.show_title_frame.inner, font = ("Helvetica", 46), padx = 10,
            text = "placeholder text", width = 1000, image = self._pixel,
            compound = "left", anchor = "w", height = 100
            )
        self.show_title.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.show_title_frame.columnconfigure(0, weight = 1)
        self.show_title_frame.rowconfigure(0, weight = 1)

        self.btn_add_new = PolygonButton(
            self.widget_frame, text = "+", command = self.add_new,
            width = 130, anchor = "center", font = ("Calibri", 45),
            height = 100
            )
        self.season_display = SeasonCounter(
            self.widget_frame, bg = c.COLOUR_TV_BACKGROUND, width = 200,
            height = 100
            )
        self.season_display.bind("<<SeasonChange>>", self.update_table)

        self.btn_increment = PolygonButton(
            self.widget_frame, text = "+", command = futil.null_function,
            width = 40, anchor = "center", repeatinterval = 100,
            repeatdelay = 500, height = 15
            )
        self.btn_increment.bind("<1>", self.increment)
        self.btn_increment.bind("<Shift-1>", self.increment_all)
        self.btn_deincrement = PolygonButton(
            self.widget_frame, text = "-", command = futil.null_function,
            width = 40, anchor = "center", repeatinterval = 100,
            repeatdelay = 500, height = 15
            )
        self.btn_deincrement.bind("<1>", self.decrement)
        self.btn_deincrement.bind("<Shift-1>", self.decrement_all)

        self.episode_table = EpisodeTable(self.widget_frame)
        self.episode_table.table.bind("<Double-1>", self._double_episode_row)

        self.btn_save = PolygonButton(
            self.widget_frame, text = "💾", command = self._click_save,
            width = 130, anchor = "center", font = ("Calibri", 30)
            )
        self.btn_discard = PolygonButton(
            self.widget_frame, text = "🗑", command = self._click_discard,
            width = 130, anchor = "center", font = ("Calibri", 30),
            )
        self.btn_refresh = PolygonButton(
            self.widget_frame, text = "⟳", command = self._click_refresh,
            width = 130, anchor = "center", font = ("Calibri", 30),
            )
        self.btn_download = PolygonButton(
            self.widget_frame, text = "", command = self._click_download,
            width = 130, anchor = "center", font = ("Calibri", 30),
            )
        self.btn_search = PolygonButton(
            self.widget_frame, text = "🔎", command = self._click_search,
            width = 130, anchor = "center", font = ("Calibri", 30),
            )
        self.btn_random = PolygonButton(
            self.widget_frame, text = "", command = self._click_random,
            width = 130, anchor = "center", font = ("Calibri", 30),
            )
        self.btn_further_details = PolygonButton(
            self.widget_frame, text = "xx",
            command = self._click_further_details, width = 130,
            anchor = "center", font = ("Calibri", 30),
            )

        self.completion_tracker = CompletionTracker(
            self.widget_frame, width = 240
            )

        widgets = {
            1: {'widget': self.episode_table,
                'grid_kwargs': {**c.GRID_STICKY, "padx": (30, 30)},
                'stretch_width': True, 'stretch_width_weight': 5,
                'stretch_height': True},
            2: {'widget': self.btn_save,
                'grid_kwargs': {**c.GRID_STICKY, "pady": 1, "padx": 20}},
            3: {'widget': self.btn_discard,
                'grid_kwargs': {**c.GRID_STICKY, "pady": (1, 70), "padx": 20}},
            4: {'widget': self.btn_refresh,
                'grid_kwargs': {**c.GRID_STICKY, "pady": 1, "padx": 20}},
            5: {'widget': self.btn_download,
                'grid_kwargs': {**c.GRID_STICKY, "pady": (1, 70), "padx": 20}},
            6: {'widget': self.btn_search,
                'grid_kwargs': {**c.GRID_STICKY, "pady": 1, "padx": 20}},
            7: {'widget': self.btn_random,
                'grid_kwargs': {**c.GRID_STICKY, "pady": 1, "padx": 20}},
            8: {'widget': self.btn_further_details,
                'grid_kwargs': {**c.GRID_STICKY, "pady": 1, "padx": 20}},
            9: {'widget': self.completion_tracker,
                'grid_kwargs': {**c.GRID_STICKY, "padx": (30, 30)},
                'stretch_width': True, 'stretch_width_weight': 1,
                'stretch_height': True},
            10: {'widget': self.show_title_frame,
                'grid_kwargs': {**c.GRID_STICKY, "padx": (30, 30), "pady": (10, 30)},
                'stretch_width': True, 'stretch_width_weight': 5},
            11: {'widget': self.btn_add_new,
                'grid_kwargs': {**c.GRID_STICKY, "pady": (20, 40), "padx": 20}},
            12: {'widget': self.season_display,
                'grid_kwargs': {**c.GRID_STICKY, "padx": (30, 1), "pady": (10, 30)}},
            13: {'widget': self.btn_increment,
                'grid_kwargs': {**c.GRID_STICKY, "padx": 2, "pady": (10, 0)}},
            14: {'widget': self.btn_deincrement,
                'grid_kwargs': {**c.GRID_STICKY, "padx": 2, "pady": (0, 30)}},
            -1: {'widget_kwargs': {"bg": c.COLOUR_TV_BACKGROUND},
                'grid_kwargs': c.GRID_STICKY,
                 'stretch_height': True, 'stretch_width': True, }
            }
        self.widget_set = tka.WidgetSet(
            self.widget_frame, widgets,
            layout = [[10, 11, 12, 13],
                      [10, 11, 12, 14],
                      [1, 2, 9, 9],
                      [1, 3, 9, 9],
                      [1, 4, 9, 9],
                      [1, 5, 9, 9],
                      [1, 6, 9, 9],
                      [1, 7, 9, 9],
                      [1, 8, 9, 9],
                      [1, -1, 9, 9]]
            )
        self.widget_set.grid(row = 0, column = 0, **c.GRID_STICKY, padx = (20, 40))
        self.columnconfigure(0, weight = 1)
        self.rowconfigure(0, weight = 1)

        self.series = None
        self.title_id = self.get_startup_title_id()
        self.update_table()
        self.bind("<<SeriesChange>>", self._series_change)
        self.event_generate("<<SeriesChange>>")

    @log_class
    def add_series(self, title):
        if not imdbf.exists(title.title_id):
            """ Add a new series to the database """
            self.progress_bar = PolygonProgressBar(
                self, style = "PolygonProgress.Horizontal.TProgressbar")
            self.progress_bar.start_indeterminate()
            self.progress_bar.after(100, lambda: self._add_series(title))
            self.progress_bar.start()

        self.title_id = title.title_id
        self.update_table()
        self.event_generate("<<SeriesChange>>")

    @log_class
    def _add_series(self, title):
        """ Download episodes and add them to the database """
        # Get a title object with imdbpy.Movie object embedded
        if not hasattr(title, '_title'):
            title = imdbf.get_title(title.title_id, get_episodes = False,
                                    refresh = True)
        seasons = title.get_episodes(basic_only = True)
        imdbf.add_title(title.title_id)

        num_episodes = sum([len(season) for season in seasons.values()])
        self.progress_bar.stop_indeterminate()
        self.progress_bar.maximum = num_episodes

        for season in seasons:
            for episode in seasons[season]:
                movie = seasons[season][episode]
                try:
                    imdbf.add_title(movie.getID())
                except imdb_functions.EpisodeExistsError:
                    pass
                self.progress_bar.step(1)

    @log_class
    def confirm_tv_request(self, event = None):
        title_id = self.tv_request.get_value()
        self.tv_request.destroy()
        self.log_entry(title_id)

    @log_class
    def log_entry(self, title_id):
        # get the title object for this id
        title = imdbf.get_title(title_id, get_episodes = False,
                                refresh = False)

        if title.type in c.TV_TYPES:
            self.add_series(title)

        elif title.type in c.EPISODE_TYPES:
            self.title_id = title.series_id
            season, episode = self.get_title_season_episode(title_id)
            self.season_display.set(season, suppress_event = True)
            self.update_table()

            # dim the window in the background for better contrast
            self.dim(transparency = 0.7)

            # open the window to log the entry
            self.log_entry_window = LogEntryWindow(
                self, bg = c.COLOUR_TRANSPARENT
                )
            self.log_entry_window.title_id = title.title_id
            title_dict = title.get_dict("title")
            title_dict_subset = {
                key: title_dict[key] for key in
                ["title", "year", "director", "runtime"]
                }
            subtitle = "%s S%sE%s" % (title.series.title, season, episode)
            title_dict_subset["original_title"] = subtitle

            title_dict_subset["date"] = datetime.now().strftime("%Y-%m-%d")
            self.log_entry_window.set_text(**title_dict_subset)
            self.log_entry_window.bind("<<Destroy>>", self.undim)
            self.log_entry_window.bind("<<LogEntry>>", self.add_entry)
            self.log_entry_window.start()

    @log_class
    def get_title_season_episode(self, title_id):
        result = base.polygon_db.episodes.filter(
            {'title_id': title_id},
            return_cols = ['season', 'episode'],
            rc = 'rowdict'
            )[0]
        return (result['season'], result['episode'])

    @log_class
    def dim(self, transparency = 0.5):
        self.window.wm_attributes("-alpha", transparency)

    @log_class
    def undim(self, *args, **kwargs):
        self.dim(transparency = 1)

    @log_class
    def add_entry(self, event = None):
        entry_dict = self.log_entry_window.get_dict()
        entry_dict["title_id"] = self.log_entry_window.title_id
        self.log_entry_window.destroy()
        self.undim()
        imdbf.add_entry(**entry_dict)
        self.series = self.get_series_db()
        self.update_table()

    @log_class
    def add_new(self, *args, **kwargs):
        """ Called from the add new button (+) """
        self.tv_request = RequestTitleWindow(self, type = "tv")
        self.tv_request.bind("<<SetValue>>", self.confirm_tv_request)
        self.tv_request.bind("<<Destroy>>", self.undim)
        self.dim(transparency = 0.7)
        self.tv_request.start()

    @log_class
    def increment(self, *args, **kwargs):
        self.season_display.increment()

    @log_class
    def decrement(self, *args, **kwargs):
        self.season_display.decrement()

    @log_class
    def increment_all(self, *args, **kwargs):
        self.season_display.set(self.season_display.maximum)

    @log_class
    def decrement_all(self, *args, **kwargs):
        self.season_display.set(self.season_display.minimum)

    @log_class
    def _series_change(self, event):
        season = self.get_first_incomplete_season(self.title_id)
        self.season_display.set(season)

    @log_class
    def update_table(self, event = None, refresh = False, *args, **kwargs):
        self.episode_table.clear()
        title_id = self.title_id

        self.series = self.get_series(title_id, refresh = refresh)
        season = self.season_display.get()

        self.season_display.set_maximum(max(self.series.seasons))
        self.season_display.set_minimum(min(self.series.seasons))

        self.show_title.config(text = self.series.title)
        self.completion_tracker.update(self.series)

        try:
            episodes = self.series.seasons[season]
        except KeyError:
            episodes = self.series.seasons[list(self.series.seasons.keys())[0]]

        self.episode_table.add_episodes(episodes)

    @log_class
    def get_series_db(self):
        self.series = None
        return self.get_series(self.title_id)

    @log_class
    def get_series(self, title_id, refresh = False):
        if refresh or self.series is None:
            series = imdbf.get_series_with_entries(title_id, refresh = refresh)
            if 'unknown' in series.seasons:
                series.seasons[0] = series.seasons['unknown']
                del series.seasons['unknown']
            return series
        elif title_id != self.series.title_id:
            self.series = None
            return self.get_series(title_id, refresh = False)
        else:
            return self.series

    @log_class
    def get_startup_title_id(self):
        """ Get the series_id of the most recent logged TV entry """
        query = """ SELECT series_id FROM episodes WHERE title_id =
                    (SELECT e.title_id from entries e
                    LEFT JOIN titles t
                    ON e.title_id = t.title_id
                    WHERE t.type IN ('%s') AND e.entry_date IS NOT NULL
                    ORDER BY entry_date DESC, entry_order DESC
                    LIMIT 1) """ % "','".join(c.EPISODE_TYPES)
        result = base.polygon_db.episodes.select(query)
        return result[0][0]

    @log_class
    def get_first_incomplete_season(self, series_id):
        query = """ SELECT MIN(season) FROM episodes ep
                    LEFT JOIN entries e
                    ON ep.title_id = e.title_id
                    WHERE series_id = '%s' AND e.title_id IS NULL
                    """ % series_id
        result = base.polygon_db.episodes.select(query)[0][0]
        if result is None:
            return 1
        else:
            return int(result)

    @log_class
    def _click_save(self, event = None):
        pass

    @log_class
    def _click_discard(self, event = None):
        pass

    @log_class
    def _click_refresh(self, event = None):
        self.update_table()

    @log_class
    def _click_download(self, event = None):
        title = self.get_series(self.title_id, refresh = True)
        title.get_episodes(basic_only = True)
        # for season_number, season in title.se

    @log_class
    def _click_search(self, event = None):
        series_dict = self.get_series_list()
        self.series_list = OptionList(
            self, style = "SeriesList.Treeview", width = 350, height = 700,
            title = "Series"
            )
        self.series_list.set(series_dict)
        self.series_list.bind("<<SetValue>>", self._series_select)
        self.series_list.start()

    @log_class
    def _series_select(self, event = None):
        series_id = self.series_list.get()
        self.title_id = series_id
        self.series_list.destroy()
        self.update_table()
        self.event_generate("<<SeriesChange>>")

    @log_class
    def get_series_list(self) -> dict:
        query = """SELECT title_id, (title || ' (' || CAST(year AS NVARCHAR(4))
                   || ')') AS title FROM titles
                   WHERE type IN ('%s')""" % "', '".join(c.TV_TYPES)
        result = base.polygon_db.titles.select(query)
        result_dict = {title_id: title for title_id, title in result}
        return result_dict

    @log_class
    def _click_random(self, event = None):
        series = self.get_series_list()
        series_id = random.choice(list(series))
        self.title_id = series_id
        self.update_table()
        self.event_generate("<<SeriesChange>>")

    @log_class
    def _click_further_details(self, event = None):
        pass

    @log_class
    def _double_episode_row(self, event):
        title_id = self.episode_table.table.events["<Double-1>"]["row"]
        self.log_entry(title_id)


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    style.configure('entrytag.TMenubutton', font = ("Helvetica", 16))
    root.configure(bg = c.COLOUR_FILM_BACKGROUND, pady = 30)
    root.columnconfigure(0, weight = 1)
    root.rowconfigure(0, weight = 1)
    ft = TvTracker(root, bg = c.COLOUR_TV_BACKGROUND)
    ft.grid(row = 0, column = 0, **c.GRID_STICKY)

    style.configure(
        "EpisodeTable.Treeview", fieldbackground="white",
        font = ('Calibri', 20), rowheight = 40, relief = 'flat'
        )
    style.map(
        'EpisodeTable.Treeview', background=[('selected', '#F5F5F5')],
        foreground=[('selected', 'black')]
        )
    style.configure(
        "EpisodeTable.Treeview.Heading", font = ('Calibri', 20,'bold'),
        padding = 5, rowheight = 60
        )
    style.configure(
        "SeriesList.Treeview.Heading", font = ('Calibri', 15,'bold'),
        padding = 5, rowheight = 30
        )
    style.configure(
        "SeriesList.Treeview", font = ('Calibri', 12),
        padding = 5, rowheight = 20
        )
    style.layout(
            'PolygonProgress.Horizontal.TProgressbar',
            [('Horizontal.Progressbar.trough',
              {'children': [('Horizontal.Progressbar.pbar',
                             {'side': 'left', 'sticky': 'ns'})],
               'sticky': 'nswe'}),
             ('Horizontal.Progressbar.label', {'sticky': ''})])
    style.configure(
            "PolygonProgress.Horizontal.TProgressbar",
            foreground = "black", background = "midnight blue",
            bordercolor = "midnight blue", lightcolor = "midnight blue",
            darkcolor = "midnight blue", text = '0%',
            font = ('Calibri', 15, 'bold')
            )

    root.mainloop()
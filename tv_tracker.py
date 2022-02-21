# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 20:40:22 2022

@author: marcu
"""
import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkf
from datetime import datetime

from mh_logging import log_class
import tk_arrange as tka
import described_widgets as dw
import constants as c
import base
import futil
from imdb_functions import imdbf
from widgets import FlexLabel, Counter, Padding, RangeDisplay, PolygonButton
from log_entry import LogEntryWindow
# from film_tracker import RequestFilmWindow

log_class = log_class(c.LOG_LEVEL)
# log_class = log_class("min")

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
    def set(self, count):
        self.season = int(count)
        count = self.enforce_bounds(count)
        self.counter.config(text = "Season %s" % count)
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
            1: {"header": "Season", "width": 110,
                "stretch": True, "anchor": "center"},
            2: {"header": "#", "width": 40,
                "stretch": True, "anchor": "center"},
            3: {"header": "%", "width": 80,
                "stretch": True, "anchor": "center"},
            }
        self.table = dw.SimpleTreeview(
            self.inner, columns, style = "EpisodeTable.Treeview", edit = True
            )
        self.table.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

    @log_class
    def update(self, series):
        self.table.clear()
        for number, season in series.seasons.items():
            self.table.insert(
                "", "end", iid = number, text = number, values = (
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
            2: {"header": "Episode name", "width": 800,
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
            self.inner, columns, style = "EpisodeTable.Treeview", edit = True,
            edit_focus_lost_confirm = True, edit_font = ('Calibri', 20)
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

        for i, title in enumerate(titles):
            values = self.get_values(title)
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
                'grid_kwargs': {**c.GRID_STICKY, "padx": (30, 1), "pady": (10, 30)},
                'stretch_width': True, 'stretch_width_weight': 0},
            13: {'widget': self.btn_increment,
                'grid_kwargs': {**c.GRID_STICKY, "padx": 2, "pady": (10, 0)}},
            14: {'widget': self.btn_deincrement,
                'grid_kwargs': {**c.GRID_STICKY, "padx": 2, "pady": (0, 30)}},
            -1: {'widget_kwargs': {"bg": c.COLOUR_TV_BACKGROUND},
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
        self.rowconfigure(1, weight = 1)

        self.series = None
        self.title_id = self.get_startup_title_id()
        season = self.get_first_incomplete_series(self.title_id)
        self.season_display.set(season)

        self.update_table()

    @log_class
    def log_entry(self, event = None):
        return
        title_id = self.film_request.get_value()

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
        self.query_data()
        self.set_counter_range()

    @log_class
    def add_new(self, *args, **kwargs):
        pass #TODO open film request window
        # self.log_entry()

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
    def update_table(self, *args, **kwargs):
        self.episode_table.clear()
        title_id = self.title_id
        season = self.season_display.get()
        series = self.get_series(title_id)

        self.season_display.set_maximum(max(series.seasons))
        self.season_display.set_minimum(min(series.seasons))

        self.show_title.config(text = series.title)
        self.completion_tracker.update(series)
        episodes = series.seasons[season]

        self.episode_table.add_episodes(episodes)

    @log_class
    def get_series(self, title_id, refresh = False):
        if refresh or self.series is None:
            series = imdbf.get_series_with_entries(title_id, refresh)
            if 'unknown' in series.seasons:
                series.seasons[0] = series.seasons['unknown']
                del series.seasons['unknown']
            return series
        elif title_id != series.title_id:
            return self.get_series(title_id, refresh = True)
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
    def get_first_incomplete_series(self, series_id):
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
        pass

    @log_class
    def _click_download(self, event = None):
        pass

    @log_class
    def _click_search(self, event = None):
        pass

    @log_class
    def _click_random(self, event = None):
        pass

    @log_class
    def _click_further_details(self, event = None):
        pass


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

    root.mainloop()
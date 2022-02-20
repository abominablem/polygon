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
from futil import get_tk, format_time
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

        self.counter = FlexLabel(
            self.counter_frame.inner, text = "Season 1",
            font = self.font_count, padx = 25, image = self._pixel,
            compound = "center", anchor = "center"
            )

        self.counter.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

    @log_class
    def set(self, count):
        self.season = int(count)
        count = self.enforce_bounds(count)
        self.counter.config(text = "Season %s" % count)
        # self.fit_text()

    @log_class
    def get(self, *args, **kwargs):
        return self.season

    @log_class
    def set_maximum(self, maximum):
        self.maximum = maximum
        if self.upper > maximum:
            self.increment(maximum - self.upper)

    @log_class
    def set_minimum(self, minimum):
        self.minimum = minimum
        if self.lower < minimum:
            self.increment(self.lower - minimum)

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
        self.style = ttk.Style()
        self.style.configure(
            "EpisodeTable.Treeview", fieldbackground="white",
            font=('Calibri', 20), rowheight=40, borderwidth = 10,
            relief = 'flat'
            )
        self.style.map(
            'EpisodeTable.Treeview', background=[('selected', '#F5F5F5')],
            foreground=[('selected', 'black')]
            )
        self.style.configure(
            "EpisodeTable.Treeview.Heading", font = ('Calibri', 20,'bold'),
            padding = 5, rowheight = 60
            )

        columns = {
            1: {"header": "#", "width": 70,
                "stretch": False, "anchor": "center"},
            2: {"header": "Episode name", "width": 800,
                "stretch": True, "anchor": "w"},
            3: {"header": "Watched?", "width": 200,
                "stretch": False, "anchor": "center"},
            4: {"header": "Date watched", "width": 270,
                "stretch": False, "anchor": "center"},
            5: {"header": "Rating", "width": 150,
                "stretch": False, "anchor": "center"},
            6: {"header": "Runtime", "width": 150,
                "stretch": False, "anchor": "center"},
            }
        self.table = dw.SimpleTreeview(
            self.inner, columns, style = "EpisodeTable.Treeview")
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
            return (title.title, "Yes", date, rating,
                    format_time(title.runtime, unit = "minutes"))
        else:
            return (title.title, "No", "", "",
                    format_time(title.runtime, unit = "minutes"))


    @log_class
    def clear(self):
        self.table.clear()

class TvTracker(tk.Frame):
    @log_class
    def __init__(self, master, *args, **kwargs):
        self._during_startup = True
        super().__init__(master, *args, **kwargs)
        self.window = get_tk(self)

        """ Build header with buttons and summary """
        self._pixel = tk.PhotoImage(width = 1, height = 1)
        self.header_frame = tk.Frame(self, bg = c.COLOUR_TV_BACKGROUND)
        self.show_title_frame = base.TrimmedFrame(self.header_frame)
        self.show_title = tk.Label(
            self.show_title_frame.inner, font = ("Helvetica", 46), padx = 10,
            text = "placeholder text", width = 1000, image = self._pixel,
            compound = "left", anchor = "w"
            )
        self.show_title.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.show_title_frame.columnconfigure(0, weight = 1)
        self.show_title_frame.rowconfigure(0, weight = 1)

        self.btn_add_new = PolygonButton(
            self.header_frame, text = "⠀+⠀", command = self.add_new,
            width = 130, anchor = "center", font = ("Calibri", 45),
            )
        self.season_display = SeasonCounter(
            self.header_frame, bg = c.COLOUR_TV_BACKGROUND, width = 200
            )
        self.season_display.bind("<<SeasonChange>>", self.update_table)

        self.btn_increment = PolygonButton(
            self.header_frame, text = "+", command = self.increment,
            width = 40, anchor = "center", repeatinterval = 100,
            repeatdelay = 500, height = 15
            )
        self.btn_increment.bind("<Shift-1>", self.increment_all)
        self.btn_deincrement = PolygonButton(
            self.header_frame, text = "-", command = self.decrement,
            width = 40, anchor = "center", repeatinterval = 100,
            repeatdelay = 500, height = 15
            )
        self.btn_deincrement.bind("<Shift-1>", self.decrement_all)

        widgets = {
            1: {'widget': self.show_title_frame,
                'grid_kwargs': {**c.GRID_STICKY, "padx": (30, 30)},
                'stretch_width': True, 'stretch_width_weight': 5},
            2: {'widget': self.btn_add_new,
                'grid_kwargs': {**c.GRID_STICKY, "pady": 10}},
            3: {'widget': self.season_display,
                'grid_kwargs': {**c.GRID_STICKY, "padx": (30, 1)},
                'stretch_width': True, 'stretch_width_weight': 1},
            4: {'widget': self.btn_increment,
                'grid_kwargs': {**c.GRID_STICKY, "padx": 2}},
            5: {'widget': self.btn_deincrement,
                'grid_kwargs': {**c.GRID_STICKY, "padx": 2}}
            }

        self.header = tka.WidgetSet(self.header_frame, widgets,
                                    layout = [[1, 2, 3, 4], [1, 2, 3, 5]])
        self.header.grid(row = 0, column = 0, **c.GRID_STICKY,
                          pady = (10, 20), padx = (20, 50))

        self.body_frame = tk.Frame(self, bg = c.COLOUR_TV_BACKGROUND)
        self.episode_table = EpisodeTable(self.body_frame)

        widgets = {
            1: {'widget': self.episode_table,
                'grid_kwargs': {**c.GRID_STICKY, "padx": (30, 30)},
                'stretch_width': True, 'stretch_width_weight': 5},
            # 2: {'widget': self.btn_add_new,
            #     'grid_kwargs': {**c.GRID_STICKY, "pady": 10}},
            # 3: {'widget': self.season_display,
            #     'grid_kwargs': {**c.GRID_STICKY, "padx": (30, 1)},
            #     'stretch_width': True, 'stretch_width_weight': 1},
            # 4: {'widget': self.btn_increment,
            #     'grid_kwargs': {**c.GRID_STICKY, "padx": 2}},
            # 5: {'widget': self.btn_deincrement,
            #     'grid_kwargs': {**c.GRID_STICKY, "padx": 2}}
            }
        self.body = tka.WidgetSet(self.body_frame, widgets,
                                  layout = [[1], [1]])
        self.body.grid(row = 1, column = 0, **c.GRID_STICKY, padx = (20, 20))

        self.columnconfigure(0, weight = 1)
        self.rowconfigure(0, weight = 1)
        self.rowconfigure(1, weight = 1)

        self.title_id = self.get_startup_title_id()
        season = self.get_first_incomplete_series(self.title_id)
        self.season_display.set(season)

        self.update_table()

    @log_class
    def dim(self, transparency = 0.5):
        self.window.wm_attributes("-alpha", transparency)

    @log_class
    def undim(self, *args, **kwargs):
        self.dim(transparency = 1)

    @log_class
    def add_new(self, *args, **kwargs):
        pass

    @log_class
    def increment(self, *args, **kwargs):
        pass

    @log_class
    def decrement(self, *args, **kwargs):
        pass

    @log_class
    def increment_all(self, *args, **kwargs):
        pass

    @log_class
    def decrement_all(self, *args, **kwargs):
        pass

    @log_class
    def update_table(self, *args, **kwargs):
        title_id = self.title_id
        season = self.season_display.get()
        entries = self.get_entries(title_id, season)
        self.episode_table.add_episodes(entries)

    @log_class
    def get_entries(self, title_id, season):
        self.episode_table.clear()
        entries = imdbf.get_series_with_entries(title_id).seasons[season]
        return entries

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


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.configure('entrytag.TMenubutton', font = ("Helvetica", 16))
    root.configure(bg = c.COLOUR_FILM_BACKGROUND, pady = 30)
    root.columnconfigure(0, weight = 1)
    root.rowconfigure(0, weight = 1)
    ft = TvTracker(root, bg = c.COLOUR_TV_BACKGROUND)
    ft.grid(row = 0, column = 0, **c.GRID_STICKY)
    root.mainloop()
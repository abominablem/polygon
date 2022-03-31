# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 22:10:31 2022

@author: marcu
"""

import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import tkinter as tk
from tkinter import ttk
from datetime import datetime

from mh_logging import log_class
import tk_arrange as tka
import constants as c
from futil import get_tk, format_time
from imdb_functions import imdbf
from widgets import (TitleModule, Counter, Padding, RangeDisplay, PolygonButton,
                     RequestTitleWindow, HoverIconPath)
from log_entry import LogEntryWindow

log_class = log_class(c.LOG_LEVEL)

class FilmTracker(tk.Frame):
    @log_class
    def __init__(self, master, *args, **kwargs):
        self._during_startup = True
        super().__init__(master, *args, **kwargs)
        self.window = get_tk(self)
        self.columnconfigure(0, weight = 1)
        self.rowconfigure(1, weight = 1)

        """ Build header with buttons and summary """
        self.header_frame = tk.Frame(
            self, bg = c.COLOUR_FILM_BACKGROUND
            )
        self.counter = Counter(
            self.header_frame, bg = c.COLOUR_FILM_BACKGROUND,
            height = c.DM_FILM_HEADER_HEIGHT
            )
        self.padding_left = Padding(
            self.header_frame, height = c.DM_FILM_HEADER_HEIGHT
            )

        self.btn_add_new = PolygonButton(
            self.header_frame, text = "⠀+⠀", command = self.add_new,
            height = c.DM_FILM_HEADER_HEIGHT, width = 130, anchor = "center",
            font = ("Calibri", 45),
            )
        self.btn_toggle_rewatch = PolygonButton(
            self.header_frame, text = "⟳", command = self.toggle_rewatch,
            toggleable = True, height = c.DM_FILM_HEADER_HEIGHT,
            width = 130, font = ("Calibri", 45), anchor = "center",
            )
        self.btn_toggle_time = PolygonButton(
            self.header_frame, text = "", command = self.toggle_time,
            toggleable = True, height = c.DM_FILM_HEADER_HEIGHT,
            width = 130, anchor = "center",
            )

        self.padding_middle = Padding(
            self.header_frame, height = c.DM_FILM_HEADER_HEIGHT
            )

        self.last_range_change = datetime.min
        self.btn_deincrement = PolygonButton(
            self.header_frame, text = "⭠", command = self.deincrement,
            height = c.DM_FILM_HEADER_HEIGHT, width = 65, anchor = "center",
            repeatinterval = 100, repeatdelay = 500
            )
        self.btn_deincrement.bind("<Shift-1>", self.deincrement_all)
        self.range_display = RangeDisplay(
            self.header_frame, width = 300, height = c.DM_FILM_HEADER_HEIGHT,
            minimum = 1,  mindiff = 0
            )
        self.btn_increment = PolygonButton(
            self.header_frame, text = "⭢", command = self.increment,
            height = c.DM_FILM_HEADER_HEIGHT, width = 65, anchor = "center",
            repeatinterval = 100, repeatdelay = 500
            )
        self.btn_increment.bind("<Shift-1>", self.increment_all)

        self.padding_right = Padding(
            self.header_frame, width = 200, height = c.DM_FILM_HEADER_HEIGHT
            )

        self.watchlist_icon = HoverIconPath(
            self.header_frame, bg = c.COLOUR_FILM_BACKGROUND, dimensions = (90, 90),
            standard = r".\common\watchlist_outlined.png",
            hover = r".\common\watchlist_outlined_hover.png"
            )
        self.watchlist_icon.bind("<1>", self._click_watchlist_icon)

        widgets = {1: {'widget': self.counter,
                       'grid_kwargs': {**c.GRID_STICKY, "padx": (30, 100)}},
                   2: {'widget': self.padding_left,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True},
                   3: {'widget': self.btn_add_new,
                       'grid_kwargs': {**c.GRID_STICKY, "pady": 0, "padx": 2}},
                   4: {'widget': self.btn_toggle_rewatch,
                       'grid_kwargs': {**c.GRID_STICKY, "pady": 0, "padx": 2}},
                   5: {'widget': self.btn_toggle_time,
                       'grid_kwargs': {**c.GRID_STICKY, "pady": 0, "padx": 2}},
                   6: {'widget': self.padding_middle,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True,},
                   7: {'widget': self.btn_deincrement,
                       'grid_kwargs': {**c.GRID_STICKY, "pady": 10, "padx": 1}},
                   8: {'widget': self.range_display,
                       'grid_kwargs': c.GRID_STICKY},
                   9: {'widget': self.btn_increment,
                       'grid_kwargs': {**c.GRID_STICKY, "pady": 10, "padx": 2}},
                   10: {'widget': self.padding_right,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True},
                   11: {'widget': self.watchlist_icon,
                       'grid_kwargs': {**c.GRID_STICKY, "padx": (0, 100)}},
                   }

        self.header = tka.WidgetSet(self.header_frame, widgets,
                                    layout = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        self.header.grid(row = 0, column = 0, **c.GRID_STICKY,
                         pady = (10, 20))
        self.header_frame.grid(row = 0, column = 0, **c.GRID_STICKY,
                               padx = (20, 0), pady = (20, 0))
        self.header_frame.columnconfigure(0, weight = 1)

        """ Get data from database """
        self.query_data()

        """ Create TitleModules """
        self.titlemod_frame = tk.Frame(
            self, bg = c.COLOUR_FILM_BACKGROUND
            )
        self.titlemod_frame.grid(row = 1, column = 0, **c.GRID_STICKY)
        self.titlemod_frame.columnconfigure(0, weight = 1)
        self.title_modules = {}
        for i in range(c.INT_FILM_TITLES):
            self.add_title_module()
        self.set_counter_range()
        self.set_title_text()

        self._last_configured = datetime.min
        self._bind_configure()

        # allow time for widgets to be placed and settle before formally
        # ending startup
        self.after(1000, self.end_startup)

    @log_class
    def end_startup(self, *args, **kwargs):
        self._during_startup = False

    @log_class
    def query_data(self):
        self.get_ranked_entries()
        self.get_film_counts()
        self.range_display.set_maximum(max(self.ranked_entries))
        self.counter.set_counter(self.count_films)

    @log_class
    def set_counter(self):
        if self.btn_toggle_time.toggle_on:
            self.counter.set_counter(
                format_time(self.total_runtime, unit = 'minutes',
                round_to = 'minutes')
                )
        elif self.btn_toggle_rewatch.toggle_on:
            self.counter.set_counter(self.count_entries)
        else:
            self.counter.set_counter(self.count_films)

    @log_class
    def get_ranked_entries(self):
        """ Get dictionary of all entries, ranked in decreasing order of
        watch date """
        self.ranked_entries = imdbf.get_entry_by_rank(
            rank = None, type = "movie", rewatch = False
            )
        self.ranked_entries_rewatches = imdbf.get_entry_by_rank(
            rank = None, type = "movie", rewatch = True
            )

    @log_class
    def get_film_counts(self):
        """ Query the number of watched films and logged entries """
        movie_types = "', '".join(c.MOVIE_TYPES)
        self.count_films = imdbf.db.entries.select(
            """ SELECT COUNT(DISTINCT e.title_id) FROM entries e INNER JOIN
            titles t ON e.title_id = t.title_id WHERE t.type IN
            ('%s') """ % movie_types)[0][0]
        self.count_entries = imdbf.db.entries.select(
            """ SELECT COUNT(*) FROM entries e INNER JOIN
            titles t ON e.title_id = t.title_id WHERE t.type IN
            ('%s') AND e.entry_date IS NOT NULL"""
            % movie_types)[0][0]
        self.total_runtime = int(imdbf.db.entries.select(
            """ SELECT SUM(t.runtime) FROM entries e LEFT JOIN titles t
            ON e.title_id = t.title_id WHERE t.type IN ('%s') """
            % movie_types)[0][0])

    @log_class
    def set_counter_range(self):
        """ Set the counter range based on the current values and the number
        of title modules displayed """
        lower = self.range_display.lower
        num_titlemods = len(self.title_modules)
        self.range_display.mindiff = num_titlemods - 1
        self.range_display.set_range(lower, lower + num_titlemods - 1)

    @log_class
    def set_title_text(self):
        """ Set the text of the title modules based on the current displayed
        range """
        if self.btn_toggle_rewatch.toggle_on:
            entries = self.ranked_entries_rewatches
        else:
            entries = self.ranked_entries

        ranks = self.range_display.get_range()
        for order, rank in enumerate(ranks):
            try:
                self.title_modules[order].set_text(**entries[rank])
            except:
                self.title_modules[order].set_text(rewatch = False)

    @log_class
    def update_title_modules(self):
        """ Update the text of all displayed title modules """
        self.set_counter_range()
        self.set_title_text()

    @log_class
    def add_new(self, *args, **kwargs):
        """ Called from the add new button (+) """
        self.film_request = RequestTitleWindow(self)
        self.film_request.bind("<<SetValue>>", self.log_entry)
        self.film_request.bind("<<Destroy>>", self.undim)
        self.dim(transparency = 0.7)
        self.film_request.start()

    @log_class
    def log_entry(self, event = None):
        title_id = self.film_request.get_value()
        # get the title object for this id
        title = imdbf.get_title(title_id)
        self.film_request.destroy()

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
            ["title", "original_title", "year", "director", "runtime"]
            }
        title_dict_subset["date"] = datetime.now().strftime("%Y-%m-%d")
        self.log_entry_window.set_text(**title_dict_subset)
        self.log_entry_window.bind("<<Destroy>>", self.undim)
        self.log_entry_window.bind("<<LogEntry>>", self.add_entry)
        self.log_entry_window.start()

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
        self.set_title_text()

    @log_class
    def toggle_rewatch(self, *args, **kwargs):
        """ Toggle whether to include rewatches in the diary/counter or not """
        if self.btn_toggle_rewatch.toggle_on:
            self.range_display.set_maximum(max(self.ranked_entries_rewatches))
        else:
            self.range_display.set_maximum(max(self.ranked_entries))
        self.set_counter()
        self.update_title_modules()

    @log_class
    def toggle_time(self, *args, **kwargs):
        """ Toggle the icon displayed on the counter """
        if self.btn_toggle_time.toggle_on:
            self.counter.set_icon(type = "time")
        else:
            self.counter.set_icon(type = "count")
        self.set_counter()

    @log_class
    def count_title_modules(self):
        """ Get the number of title modules currently displayed """
        return len(self.title_modules)

    @log_class
    def deincrement(self, *args, **kwargs):
        """ Increment the range display so that the previous set of titles is
        displayed """
        self.range_display.increment(-1*self.count_title_modules())
        self.update_title_modules()

    @log_class
    def increment(self, *args, **kwargs):
        """ Increment the range display so that the next set of titles is
        displayed """
        self.range_display.increment(self.count_title_modules())
        self.update_title_modules()

    @log_class
    def deincrement_all(self, *args, **kwargs):
        """ Deincrement the range display as far as possible """
        self.range_display.increment(-1*self.range_display.lower + 1)
        self.update_title_modules()

    @log_class
    def increment_all(self, *args, **kwargs):
        """ Increment the range display as far as possible """
        if self.btn_toggle_rewatch.toggle_on:
            self.range_display.increment(self.count_entries)
        else:
            self.range_display.increment(self.count_films)
        self.update_title_modules()

    @log_class
    def get_available_height(self):
        """ Get space available for title modules to be added """
        window_height = self.winfo_height()
        header_height = self.header.master.winfo_height()
        return window_height - header_height

    @log_class
    def _get_max_titlemods(self):
        """ Get maximum number of title mods that will fit based on available
        space. If called during startup, return the defined constant
        default. """
        if self._during_startup:
            return c.INT_FILM_TITLES
        else:
            titlemod_height = self.title_modules[0].winfo_height()
            available_height = self.get_available_height()
            if available_height == 0:
                return 0
            else:
                return available_height // titlemod_height

    @log_class
    def _configure(self, *args, **kwargs):
        """ Called when <Configure> event is triggered. """
        if (datetime.now() - self._last_configured).total_seconds() < 0.1:
            return
        if self._during_startup:
            return
        # Temporarily unbind and then rebind the configure callback to prevent
        # infinite loops from creating widgets inside this function
        self._unbind_configure()
        self._last_configured = datetime.now()
        if self.create_titlemods():
            self.update_title_modules()
        self._bind_configure()

    @log_class
    def _bind_configure(self, *args, **kwargs):
        self._configure_binding = self.bind(
            "<Configure>", self._configure
            )

    @log_class
    def _unbind_configure(self, *args, **kwargs):
        self.unbind("<Configure>", self._configure_binding)

    @log_class
    def _click_watchlist_icon(self, *args, **kwargs):
        print("watchlist icon clicked")

    @log_class
    def create_titlemods(self):
        """ Add or remove title modules based on the current number and
        available space. Return True if the number of title modules has
        changed """
        # Always keep at least 1 title mod present
        max_titlemods = max(self._get_max_titlemods(), 1)
        num_titlemods = self.count_title_modules()
        # add new title modules until max number is reached
        if num_titlemods < max_titlemods:
            for i in range(max_titlemods - num_titlemods):
                self.add_title_module()
            return True
        elif num_titlemods == max_titlemods:
            return False
        # or remove until max number is reached
        else:
            removals = [i for i in self.title_modules if i+1 >= num_titlemods]
            for i in removals:
                self.remove_title_module(i)
            return True

    @log_class
    def add_title_module(self):
        """ Add a new title module to the end """
        i = self.count_title_modules()
        tm = TitleModule(
            self.titlemod_frame, bg = c.COLOUR_FILM_BACKGROUND, padx = 10,
            pady = 20
            )
        self.title_modules[i] = tm
        tm.grid(row = i, column = 0, **c.GRID_STICKY)

    @log_class
    def remove_title_module(self, index = None):
        """ Remove a specific TitleModule, defaulting to the last one """
        if index is None:
            index = max(self.title_modules)
        self.title_modules[index].grid_forget()
        del self.title_modules[index]


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.configure('entrytag.TMenubutton', font = ("Helvetica", 16))
    root.configure(bg = c.COLOUR_FILM_BACKGROUND, pady = 30)
    # root.overrideredirect(True)
    root.columnconfigure(0, weight = 1)
    ft = FilmTracker(root, bg = c.COLOUR_FILM_BACKGROUND)
    ft.grid(row = 0, column = 0, **c.GRID_STICKY)
    root.mainloop()
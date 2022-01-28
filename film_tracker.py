# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 22:10:31 2022

@author: marcu
"""

import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import tkinter as tk
from widgets import TitleModule

from mh_logging import log_class
import tk_arrange as tka
import constants as c
import base
import imdb_functions

imdbf = imdb_functions.IMDbFunctions()
log_class = log_class(c.LOG_LEVEL)

class FilmCounter(tk.Frame):
    @log_class
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.counter_frame = base.TrimmedFrame(self)
        self.counter_frame.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.counter_frame.columnconfigure(0, weight = 1)
        self.counter_frame.rowconfigure(0, weight = 1)

        self._pixel = tk.PhotoImage(width = 1, height = 1)

        font_icon = ("Calibri", 36)
        font_count = ("Calibri", 32)
        self.icon = tk.Label(
            self.counter_frame.inner, text = "#", font = font_icon,
            padx = 15, image = self._pixel, compound = "center", width = 35
            )
        self.icon.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.counter_frame.inner.columnconfigure(0, weight = 1)
        self.counter_frame.inner.rowconfigure(0, weight = 1)

        self.count = tk.Label(
            self.counter_frame.inner, text = "970", font = font_count,
            padx = 25, image = self._pixel, compound = "center", width = 100
            )
        self.count.grid(row = 0, column = 1, **c.GRID_STICKY)
        self.counter_frame.inner.columnconfigure(1, weight = 1)

        self.rowconfigure(0, weight = 1)

    @log_class
    def set_counter(self, count):
        self.counter.config(text = count)

    @log_class
    def set_icon(self, type):
        if type == "count":
            self.icon.config(text = "#")
        elif type == "time":
            self.icon.config(text = "")
        else:
            raise ValueError

class RangeDisplay(tk.Frame):
    @log_class
    def __init__(self, master, minimum = 1, maximum = None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.minimum = -9223372036854775807 if minimum is None else minimum
        self.maximum = 9223372036854775807 if maximum is None else maximum

        self.columnconfigure(0, weight = 1)
        self.rowconfigure(0, weight = 1)

        self.bordered_frame = base.TrimmedFrame(self)
        self.bordered_frame.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.bordered_frame.columnconfigure(0, weight = 1)
        self.bordered_frame.rowconfigure(0, weight = 1)

        font_range = ("Calibri", 36)
        self.range = tk.Label(
            self.bordered_frame.inner, font = font_range, padx = 40
            )
        self.range.columnconfigure(0, weight = 1)
        self.range.rowconfigure(0, weight = 1)
        self.range.grid(row = 0, column = 0, **c.GRID_STICKY)

        self.lower, self.upper = 1, 5
        self.set_range(self.lower, self.upper)

    @log_class
    def set_range(self, lower = None, upper = None):
        if not lower is None: self.lower = lower
        if not upper is None: self.upper = upper
        self.range.config(text = '%s - %s' % (self.lower, self.upper))

    @log_class
    def increment(self, increment):
        lower = self.enforce_bounds(self.lower + increment)
        upper = self.enforce_bounds(self.upper + increment)
        self.set_range(lower, upper)

    def enforce_bounds(self, value):
        return max(self.minimum, min(self.maximum, value))

class PolygonButton(tk.Button):
    @log_class
    def __init__(self, master, pixels = True, toggleable = False,
                 *args, **kwargs):
        if pixels:
            self._pixel = tk.PhotoImage(width = 1, height = 1)
            kwargs.setdefault("image", self._pixel)
            kwargs.setdefault("compound", "center")
        kwargs.setdefault("font", ("Helvetica", 36))
        kwargs.setdefault("padx", 10)
        kwargs.setdefault("fg", "black")
        super().__init__(master, *args, **kwargs)

        self.toggleable = toggleable
        if toggleable:
            self.bind("<1>", self._click)
            self.toggle_on = False

    def _click(self, *args, **kwargs):
        self.toggle_on = not self.toggle_on
        if self.toggle_on:
            self.config(fg = "lime green")
        else:
            self.config(fg = "black")

class Padding(tk.Label):
    @log_class
    def __init__(self, master, pixels = True, *args, **kwargs):
        if pixels:
            self._pixel = tk.PhotoImage(width = 1, height = 1)
            kwargs.setdefault("image", self._pixel)
        kwargs["bg"] = c.COLOUR_FILM_BACKGROUND
        kwargs["text"] = ""
        super().__init__(master, *args, **kwargs)

class FilmTracker:
    @log_class
    def __init__(self, master):
        self.master = master

        """ Build header with buttons and summary """
        self.header_frame = tk.Frame(
            self.master, bg = c.COLOUR_FILM_BACKGROUND
            )
        self.counter = FilmCounter(
            self.header_frame, bg = c.COLOUR_FILM_BACKGROUND,
            height = c.DM_FILM_HEADER_HEIGHT
            )
        self.padding_left = Padding(
            self.header_frame, width = 150, height = c.DM_FILM_HEADER_HEIGHT
            )

        self.btn_add_new = PolygonButton(
            self.header_frame, text = "⠀+⠀", command = self.add_new,
            height = c.DM_FILM_HEADER_HEIGHT, width = 100, anchor = "center",
            font = ("Calibri", 45)
            )
        self.btn_toggle_rewatch = PolygonButton(
            self.header_frame, text = "⟳", command = self.toggle_rewatch,
            toggleable = True, height = c.DM_FILM_HEADER_HEIGHT,
            width = 100, font = ("Calibri", 45), anchor = "center",
            )
        self.btn_toggle_time = PolygonButton(
            self.header_frame, text = "", command = self.toggle_time,
            toggleable = True, height = c.DM_FILM_HEADER_HEIGHT,
            width = 100, anchor = "center",
            )

        self.padding_middle = Padding(
            self.header_frame, width = 150, height = c.DM_FILM_HEADER_HEIGHT
            )

        self.increment = 5
        self.btn_deincrement = PolygonButton(
            self.header_frame, text = "⭠", command = self.deincrement,
            height = c.DM_FILM_HEADER_HEIGHT, width = 65, anchor = "center",
            )
        self.range_display = RangeDisplay(
            self.header_frame, width = 250, height = c.DM_FILM_HEADER_HEIGHT,
            minimum = 1, maximum = 1000 #TODO
            )
        self.btn_increment = PolygonButton(
            self.header_frame, text = "⭢", command = self.increment,
            width = 65, height = c.DM_FILM_HEADER_HEIGHT, anchor = "center",
            )

        self.padding_right = Padding(
            self.header_frame, width = 200, height = c.DM_FILM_HEADER_HEIGHT
            )

        widgets = {1: {'widget': self.counter,
                       'grid_kwargs': {**c.GRID_STICKY, "padx": (0, 100)}},
                   2: {'widget': self.padding_left,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True},
                   3: {'widget': self.btn_add_new,
                       'grid_kwargs': {**c.GRID_STICKY, "pady": 10, "padx": 2}},
                   4: {'widget': self.btn_toggle_rewatch,
                       'grid_kwargs': {**c.GRID_STICKY, "pady": 10, "padx": 2}},
                   5: {'widget': self.btn_toggle_time,
                       'grid_kwargs': {**c.GRID_STICKY, "pady": 10, "padx": 2}},
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
                   }

        self.header = tka.WidgetSet(self.header_frame, widgets,
                                    layout = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.header.grid(row = 0, column = 0, **c.GRID_STICKY_PADDING_SMALL)
        self.header_frame.grid(row = 0, column = 0, **c.GRID_STICKY,
                               padx = c.PADDING_MEDIUM_LEFT_ONLY)
        self.header_frame.columnconfigure(0, weight = 1)

        self.title_modules = {}
        """ Add title modules """
        for i in range(c.INT_FILM_TITLES):
            tm = TitleModule(
                self.master, bg = "black", padx = 30, pady = 20
                )
            self.title_modules[i] = tm
            tm.set_text(number = i + 1)
            tm.grid(row = i + 1, column = 0, **c.GRID_STICKY)

    def set_title_text(self):
        for order, abs_order in enumerate(
                range(self.range_display.lower, self.range_display.upper)):
            tdict = self._get_title_dict(abs_order)
            self.title_modules[order].set_text(**tdict)

    @log_class
    def add_new(self, *args, **kwargs):
        raise NotImplementedError

    @log_class
    def toggle_rewatch(self, *args, **kwargs):
        raise NotImplementedError

    @log_class
    def toggle_time(self, *args, **kwargs):
        if self.btn_toggle_time.toggle_on:
            self.counter.set_icon(type = "time")
        else:
            self.counter.set_icon(type = "count")

    @log_class
    def deincrement(self, *args, **kwargs):
        self.range_display.increment(-1*self.increment)

    @log_class
    def increment(self, *args, **kwargs):
        self.range_display.increment(self.increment)


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg = c.COLOUR_FILM_BACKGROUND, pady = 30)
    root.columnconfigure(0, weight = 1)
    ft = FilmTracker(root)
    # rd = RangeDisplay(root)
    # rd.grid(row = 0, column = 0, **c.GRID_STICKY)
    root.mainloop()
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 23 21:02:39 2022

@author: marcu
"""

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkf
from datetime import datetime
import math
import re
from PIL import Image, ImageTk

import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import tk_arrange as tka
import described_widgets as dw
from mh_logging import log_class
import constants as c
import futil as futil
import base
from imdb_functions import imdbf, standardise_id
import log_entry_tag as tagf

log_class = log_class(c.LOG_LEVEL)

class RatingDisplay(tk.Text):
    """ Display a rating out of N stars """
    @log_class
    def __init__(self, master, min_rating = 1, max_rating = 10, **kwargs):

        self.set_symbol(empty_symbol = "☆", filled_symbol = "★",
                        half_symbol = "★")
        self.set_colour(empty_colour = "#D3D3D3", filled_colour = "black",
                        half_colour = "black")
        self.set_colour_map({})

        self.min_rating = min_rating
        self.max_rating = max_rating
        self.rating = 1
        self._capture_kwarg(kwargs, "empty_symbol", "_symbol_empty")
        self._capture_kwarg(kwargs, "filled_symbol", "_symbol_filled")
        self._capture_kwarg(kwargs, "half_symbol", "_symbol_half")
        self._capture_kwarg(kwargs, "empty_colour", "_colour_empty")
        self._capture_kwarg(kwargs, "filled_colour", "_colour_filled")
        self._capture_kwarg(kwargs, "half_colour", "_colour_half")
        self._capture_kwarg(kwargs, "colour_map", "colour_map")

        kwargs = self._remove_kwargs(kwargs, [
            "empty_symbol", "filled_symbol", "empty_colour", "filled_colour",
            "colour_map", 'half_colour', 'half_symbol'
            ])

        super().__init__(master, **kwargs, height = 1, wrap = 'none',
                         state = 'disabled', relief = "flat")

        if not 'font' in kwargs:
            self.font = tkf.nametofont(self.configure('font')[-1])
        else:
            self.font = tkf.Font(self, kwargs['font'])

        # bit hacky until I can work out how to get the actual width in tk.Text
        # terms of the symbols
        self.configure(width = int(self.max_rating * 2))
        self.tag_configure("center", justify = 'center')

        # hide any selections by setting to background colour
        self.configure(selectbackground = self.cget('bg'),
                       inactiveselectbackground = self.cget('bg'))

        self.refresh()

    @log_class
    def get_width(self):
        """ Get the width of the text widget based on the maximum
        font_measure'd width of the symbols and max rating. For use when
        placing the widget in the geometry """
        widths = [self.font.measure(self._symbol_empty * self.max_rating),
                  self.font.measure(self._symbol_filled * self.max_rating)]
        return max(widths)

    @log_class
    def refresh(self):
        self.set(self.rating)

    @log_class
    def set_range(self, min = None, max = None):
        """ Set the symbols for filled and empty rating symbols """
        if not min is None: self.min_rating = min
        if not max is None: self.max_rating = max

    @log_class
    def set_symbol(self, empty_symbol = None, filled_symbol = None,
                   half_symbol = None):
        """ Set the symbols for filled and empty rating symbols """
        if not empty_symbol is None: self._symbol_empty = empty_symbol
        if not filled_symbol is None: self._symbol_filled = filled_symbol
        if not half_symbol is None: self._symbol_half = half_symbol

    @log_class
    def set_colour(self, empty_colour = None, filled_colour = None,
                   half_colour = None):
        """ Set the colours of filled and empty rating symbols """
        if not empty_colour is None: self._colour_empty = empty_colour
        if not filled_colour is None: self._colour_filled = filled_colour
        if not half_colour is None: self._colour_half = half_colour

    @log_class
    def set_colour_map(self, colour_map):
        """ Dictionary map from score to colour. Dictionary values should be
        either 1) Dictionaries with keys "empty_colour" and "filled_colour"
        (missing keys will revert to the defaults) or 2) string colour for
        "filled_colour" - "empty_colour" will revert to the default in this
        case. """

        for rating in colour_map:
            col_def = colour_map[rating]
            if isinstance(col_def, dict):
                col_def.setdefault("empty_colour", self._colour_empty)
                col_def.setdefault("filled_colour", self._colour_filled)
                col_def.setdefault("half_colour", col_def["filled_colour"])
            else:
                col_def = {"filled_colour": col_def,
                           "empty_colour": self._colour_empty,
                           "half_colour": col_def}
            colour_map[rating] = col_def
        self.colour_map = colour_map

    @log_class
    def _set_colour_tags(self):
        """ Colour the text according to rules defined so far """
        colfill = self.colour_map.get(round(self.rating), {}).get(
            "filled_colour", self._colour_filled)
        colempty = self.colour_map.get(round(self.rating), {}).get(
            "empty_colour", self._colour_empty)
        colhalf = self.colour_map.get(round(self.rating), {}).get(
            "half_colour", self._colour_half)
        self.tag_config("filled_rating", foreground = colfill)
        self.tag_config("empty_rating", foreground = colempty)
        self.tag_config("half_rating", foreground = colhalf)

    @log_class
    def _clear(self):
        """ Clear the text widget """
        self.configure(state='normal')
        self.delete(1.0, tk.END)
        self.configure(state='disabled')

    @log_class
    def set(self, rating):
        """ Set rating to be displayed """
        if not self.min_rating <= rating <= self.max_rating:
            raise ValueError("Rating value out of bounds")
        self.rating = rating
        self._clear()
        self._set_colour_tags()
        self.configure(state='normal')
        is_decimal = (int(rating) != rating)
        len_filled = int(rating)
        len_half = 1 if is_decimal else 0
        len_empty = self.max_rating - len_filled - len_half

        self.insert("end", self._symbol_filled * len_filled,
                    ["filled_rating", 'center'])
        self.insert("end", self._symbol_half * len_half,
                    ["half_rating", 'center'])
        self.insert("end", self._symbol_empty * len_empty,
                    ["empty_rating", 'center'])
        self.configure(state='disabled')

    @log_class
    def _capture_kwarg(self, dict, kw, attr):
        """ Update the attribute attr with the value in dict[kw] """
        if kw in dict:
            self.__dict__[attr] = dict[kw]

    @log_class
    def _remove_kwargs(self, dict, kws):
        """ Remove keys in list from dict if they exist """
        for kw in kws:
            if kw in dict: del dict[kw]
        return dict

    @log_class
    def enforce_bounds(self, value):
        return max(self.min_rating, min(self.max_rating, value))

    @log_class
    def get_mouseover_rating(self, event):
        x = event.x
        text_width = self._get_current_width()
        widget_width = self.winfo_width()
        x_offset = int((widget_width - text_width)/2)
        x -= x_offset
        symbol_filled_width = self.font.measure(self._symbol_filled)
        hovered_rating = math.ceil(x / symbol_filled_width)
        return hovered_rating

    @log_class
    def set_mouseover_rating(self, event):
        new_rating = self.get_mouseover_rating(event)
        self.set(self.enforce_bounds(new_rating))

    @log_class
    def _get_current_width(self):
        """ Get the width of the text currently inside the widget """
        return self.font.measure(self.get('0.1', 'end').strip())

class TitleModuleBase(tk.Frame):
    """ Bordered frame containing Date, Title, Original title, Director, Year,
    and Runtime """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        font_date = ("Calibri", 28, "bold")
        font_title = ("Calibri", 32)
        font_subtitle = ("Calibri", 22, "italic")

        self._value_dict = {
            "title": None, "original_title": None, "director": None,
            "year": None, "runtime": None, "date": None
            }

        self._original_title_text = ""

        self.date = tk.Label(
            self, bg = "white", anchor = "center", font = font_date, padx = 20,
            pady = 0, width = 10
            )
        self.title = tk.Label(
            self, bg = "white", anchor = "w", font = font_title, padx = 10,
            pady = 0, width = 40
            )
        self.original_title = tk.Label(
            self, bg = "white", anchor = "w", font = font_subtitle, padx = 10,
            pady = 0
            )
        self.director = tk.Label(
            self, bg = "white", anchor = "e", font = font_subtitle, padx = 10,
            pady = 0
            )
        self.year = tk.Label(
            self, bg = "white", anchor = "center", font = font_title,
            padx = 20, pady = 0
            )
        self.runtime = tk.Label(
            self, bg = "white", anchor = "center", font = font_subtitle,
            padx = 20, pady = 0
            )

        widgets = {1: {'widget': self.date,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': False},
                   2: {'widget': self.title,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True,},
                   3: {'widget': self.original_title,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True, 'stretch_width_weight': 2},
                   4: {'widget': self.director,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True, 'stretch_width_weight': 1},
                   5: {'widget': self.year,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': False,},
                   6: {'widget': self.runtime,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': False,},
                   }

        self.widget_set = tka.WidgetSet(
            self, widgets, layout = [[1, 2, 2, 5],
                                     [1, 3, 4, 6]])

    @log_class
    def set_text(self, **kwargs):
        self._value_dict.update(kwargs)
        for kw in kwargs:
            if kw == "runtime":
                self.runtime.config(text = self.format_runtime(kwargs[kw]))

            elif kw == "title":
                text = kwargs[kw]
                if text == self.original_title.cget('text')[1:-1]:
                    self.original_title.config(text = "")
                    self.title.config(text = text)
                else:
                    self.original_title.config(
                        text = "(%s)" % self._original_title_text
                        )
                    self.title.config(text = text)

            elif kw == "original_title":
                text = kwargs[kw]
                self._original_title_text = text
                if text == self.title.cget('text'):
                    self.original_title.config(text = "")
                else:
                    self.original_title.config(text = "(%s)" % text)

            elif kw == "date":
                self.date.config(text = self.format_date(kwargs[kw]))

            else:
                self.__dict__[kw].config(text = kwargs[kw])

    @log_class
    def format_runtime(self, runtime):
        try:
            return futil.format_time(int(runtime), "minutes")
        except ValueError:
            return "N/A"

    @log_class
    def format_date(self, date):
        return datetime.strptime(date, "%Y-%m-%d").strftime("%d %b %Y")

class TitleModule(tk.Frame):
    """ Bordered frame containing TitleModuleBase data and Rating. Optional
    number to left and rewatch indicator to right"""
    @log_class
    def __init__(self, master, include_rewatch = True, include_number = True,
                 **kwargs):
        self.master = master
        super().__init__(self.master, **kwargs)

        font_rating = ("Calibri", 36, "bold")
        font_rewatch = ("Calibri", 36)
        font_number = ("Calibri", 36)

        self.border_frame = base.TrimmedFrame(self)
        self.border_frame.columnconfigure(0, weight = 1)

        self.base_module = TitleModuleBase(self.border_frame.inner)
        self.base_module.grid(row = 0, column = 0, **c.GRID_STICKY)

        """ Title rating """
        self.rating_frame = tk.Frame(self.border_frame.inner)
        self.rating = RatingDisplay(
            self.rating_frame, font = font_rating, padx = 20
            )
        self.rating.set_colour_map(
            {1: "red", 2: "red", 3: "orange", 4: "orange", 5: "#ffbf00",
              6: "#ffbf00", 7: "lime green", 8: "lime green", 9: "forest green",
              10: "midnight blue"}
            )
        widgets = {1: {'widget': tk.Frame(self.rating_frame, bg = "white"),
                       'stretch_height': True,
                       'grid_kwargs': c.GRID_STICKY,},
                   2: {'widget': self.rating,
                       'grid_kwargs': c.GRID_STICKY,},
                   3: {'widget': tk.Frame(self.rating_frame, bg = "white"),
                       'stretch_height': True,
                       'grid_kwargs': c.GRID_STICKY,},
                    }
        self.rating_widget_set = tka.WidgetSet(
            self.rating_frame, widgets, layout = [[1], [2], [3]])
        self.rating_frame.grid(row = 0, column = 1, **c.GRID_STICKY)

        widgets = {2: {'widget': self.border_frame,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True,},
                   }
        self.include_number = include_number
        if include_number:
            self.number = tk.Label(
                self, bg = c.COLOUR_FILM_BACKGROUND, anchor = "e",
                font = font_number, padx = 40, fg = "white", width = 4
                )
            widgets[1] = {'widget': self.number, 'grid_kwargs': c.GRID_STICKY}

        self.include_rewatch = include_rewatch
        if include_rewatch:
            self.rewatch = tk.Label(
                self, bg = c.COLOUR_FILM_BACKGROUND, anchor = "center",
                font = font_rewatch, padx = 40, fg = "white", text = "⟳"
                )
            widgets[3] = {'widget': self.rewatch, 'grid_kwargs': c.GRID_STICKY}

        layout = sorted(list(widgets.keys()))
        self.widgets = tka.WidgetSet(self, widgets, layout = layout)

        self._value_dict = {
            "title": None, "original_title": None, "director": None,
            "year": None, "runtime": None, "date": None, "rating": None,
            "rewatch": None, "number": None
            }

    @log_class
    def get_dict(self):
        return self._value_dict

    @log_class
    def set_text(self, **kwargs):
        self._value_dict.update(kwargs)
        for kw in kwargs:
            if kw in ["runtime", "title", "original_title", "date", "director",
                      "year"]:
                self.base_module.set_text(**{kw: kwargs[kw]})

            elif kw == "rating":
                self.rating.set(float(kwargs[kw]))

            elif kw == "rewatch" and self.include_rewatch:
                if kwargs[kw]:
                    self.rewatch.config(fg = "white")
                else:
                    self.rewatch.config(fg = c.COLOUR_FILM_BACKGROUND)

            elif kw == "number" and self.include_number:
                self.__dict__[kw].config(text = kwargs[kw])

            else:
                self.__dict__[kw].config(text = kwargs[kw])

class TitleModuleDetailed(TitleModule):
    """ Bordered frame containing TitleModule data, plot tag, and an arbitrary
    number of other tags. Optional number to left."""
    def __init__(self, master, include_number = True, include_rewatch = True,
                 **kwargs):
        super().__init__(master, include_number = include_number,
                         include_rewatch = True, **kwargs)

        self.plot_tag = tk.Text(
            self.border_frame.inner, font = ("Calibri", 24), padx = 10, pady = 10,
            state = tk.DISABLED, fg = "black", bg = "white", wrap = tk.WORD,
            relief = "flat", height = 2
            )
        self.plot_tag.grid(row = 1, column = 0, columnspan = c.COLUMNSPAN_ALL,
                            **c.GRID_STICKY)

        " Frame for all tag widgets "
        self.tag_frame = tk.Frame(self, bg = c.COLOUR_FILM_BACKGROUND)
        self.tag_widgets = []
        self.tag_frame_components = {}

        self.tag_frame.grid(row = 1, column = 1, **c.GRID_STICKY)

        self._value_dict = {
            "title": None, "original_title": None, "director": None,
            "year": None, "runtime": None, "date": None, "rating": None,
            "rewatch": None, "number": None, "plot_tag": None
            }

    @log_class
    def _place_tag_frame_component(self, y):
        self.tag_frame_components[y].grid(row = y, column = 0, **c.GRID_STICKY)

    @log_class
    def create_tag_widgets(self, tags):
        max_width = self.tag_frame.winfo_width()
        if max_width <= 1:
            max_width = 1600
        x, y = 0, 0
        self.tag_frame_components = {
            0: tk.Frame(self.tag_frame, bg = c.COLOUR_FILM_BACKGROUND)}

        self._place_tag_frame_component(0)

        for tag_name in tags:
            for tag_value in tags[tag_name]:
                if not tag_name is None:
                    text = "%s: %s" % (tag_name, tag_value)
                else:
                    text = tag_value

                " Get the dimensions of the tag image "
                _w, width, height = tagf.text_tag(
                    text, height = 40, dimensions = True)

                "Add tags to one line until it is full, then create a new line"
                if x + width > max_width and x != 0:
                    y += 1
                    self.tag_frame_components[y] = tk.Frame(
                        self.tag_frame, bg = c.COLOUR_FILM_BACKGROUND)
                    self._place_tag_frame_component(y)
                    x = 0

                widget = HoverIconTag(self.tag_frame_components[y],
                                      value = text, height = 40,
                                      bg = c.COLOUR_FILM_BACKGROUND)
                widget.tag_width, widget.tag_height = width, height
                widget.tag_name, widget.tag_value = tag_name, tag_value

                self.tag_widgets.append(widget)
                widget.grid(row = 0, column = x, columnspan = width,
                            **c.GRID_STICKY)
                x += width

    @log_class
    def replace_tag_widgets(self, event = None):
        self.remove_tag_widgets()
        self.create_tag_widgets(self._value_dict["tags"])

    @log_class
    def remove_tag_widgets(self):
        for widget in self.tag_widgets:
            widget.grid_forget()

        for widget in self.tag_frame_components.values():
            widget.grid_forget()

    @log_class
    def set_text(self, **kwargs):
        self._value_dict.update(kwargs)
        for kw in kwargs:
            if kw  == "plot_tag":
                self.plot_tag.config(state = tk.NORMAL)
                self.plot_tag.delete(0.0, "end")
                self.plot_tag.insert(0.0, kwargs[kw])
                self.plot_tag.config(state = tk.DISABLED)
            elif kw == "tags":
                self.remove_tag_widgets()
                self.create_tag_widgets(kwargs[kw])
            else:
                super().set_text(**{kw: kwargs[kw]})
#TODO

class Counter(tk.Frame):
    @log_class
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.counter_frame = base.TrimmedFrame(self)
        self.counter_frame.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.counter_frame.columnconfigure(0, weight = 1)
        self.counter_frame.rowconfigure(0, weight = 1)

        self._pixel = tk.PhotoImage(width = 1, height = 1)

        self.font_count_size = 36
        self.font_icon = ("Calibri", 40)
        self.font_count = ("Calibri", self.font_count_size)
        self.icon = tk.Label(
            self.counter_frame.inner, text = "#", font = self.font_icon,
            padx = 15, image = self._pixel, compound = "center", width = 40
            )
        self.icon.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.counter_frame.inner.columnconfigure(0, weight = 1)
        self.counter_frame.inner.rowconfigure(0, weight = 1)

        self.counter = tk.Label(
            self.counter_frame.inner, text = "0", font = self.font_count,
            padx = 25, image = self._pixel, compound = "center", width = 130
            )

        self.font = tkf.Font(self.counter, self.font_count)

        self.counter.grid(row = 0, column = 1, **c.GRID_STICKY)
        self.counter_frame.inner.columnconfigure(1, weight = 1)

        self.rowconfigure(0, weight = 1)

    @log_class
    def set_counter(self, count):
        self.counter.config(text = count)
        self.fit_text()

    @log_class
    def set_icon(self, type):
        if type == "count":
            self.icon.config(text = "#")
        elif type == "time":
            self.icon.config(text = "")
        else:
            raise ValueError

    @log_class
    def fit_text(self, *args, **kwargs):
        text = self.counter.cget('text')
        self.counter.config(font = self.get_font(text))

    @log_class
    def get_font(self, text):
        """ Get the font needed to fit the given text into the widget """
        width = self.font.measure(text)
        widget_width = self.counter.winfo_width()

        # width is <=1 during startup
        if widget_width <= 1: return self.font_count

        font = self.font_count
        font_size = self.font_count_size
        while width > widget_width:
            font = ("Calibri", font_size)
            font_obj = tkf.Font(self.counter, font)
            width = font_obj.measure(text)
            font_size -= 1
        return font

class RangeDisplay(tk.Frame):
    @log_class
    def __init__(self, master, minimum = 1, maximum = None, mindiff = 1,
                 *args, **kwargs):
        """ Display a range X - Y, with both taking a minimum or maximum value
        and with Y - X always >= mindiff (if given) """
        super().__init__(master, *args, **kwargs)

        self.minimum = -9223372036854775807 if minimum is None else minimum
        self.maximum = 9223372036854775807 if maximum is None else maximum
        self.mindiff = mindiff

        self.columnconfigure(0, weight = 1)
        self.rowconfigure(0, weight = 1)

        self.bordered_frame = base.TrimmedFrame(self)
        self.bordered_frame.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.bordered_frame.columnconfigure(0, weight = 1)
        self.bordered_frame.rowconfigure(0, weight = 1)

        font_range = ("Calibri", 36)
        self.range = tk.Label(
            self.bordered_frame.inner, font = font_range, width = 11
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
    def set_increment(self, increment):
        self.increment = increment
        upper = self.enforce_bounds(self.lower + increment)
        self.set_range(upper = upper)

    @log_class
    def increment(self, increment):
        lower = self.enforce_bounds(self.lower + increment)
        upper = self.enforce_bounds(self.upper + increment)
        if upper - lower < self.mindiff:
            upper = self.enforce_bounds(lower + self.mindiff)
            lower = self.enforce_bounds(upper - self.mindiff)
        self.set_range(lower, upper)

    @log_class
    def enforce_bounds(self, value):
        return max(self.minimum, min(self.maximum, value))

    @log_class
    def get_range(self):
        return range(self.lower, self.upper + 1)

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

    @log_class
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

class FlexLabel(tk.Label):
    """ Label with text that fits to the size of the widget """
    @log_class
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        # get the font used in the widget as a base
        try:
            _font_argument = kwargs['font']
        except KeyError:
            _font_argument = tkf.nametofont(self.cget('font'))

        # convert to a tk.font.Font object
        used_font = self._get_font_object(_font_argument)
        self.config(font = used_font)
        self._current_font = used_font
        self._default_font = used_font.copy()
        self._default_font_size = used_font.cget('size')
        self._link = None

        self._fit_binding = self.bind("<Configure>", self._fit_text, add = "+")
        self._last_fit_text = datetime.min

    @log_class
    def _get_font_object(self, font_arg):
        if isinstance(font_arg, tkf.Font):
            return font_arg
        elif isinstance(font_arg, tuple):
            return tkf.Font(self, font_arg)
        else:
            raise ValueError("Unknown font definition used")

    @log_class
    def _fit_text(self, *args, **kwargs):
        if (datetime.now() - self._last_fit_text).total_seconds() < 0.15:
            return

        self._last_fit_text = datetime.now()
        self._get_font(self.cget('text'))
        self.event_generate("<<FitText>>")

    @log_class
    def _get_font(self, text = None):
        """ Get the font needed to fit the given text into the widget. If
        text is None, return the currently used font. """
        if text is None:
            return self._current_font

        width = self._default_font.measure(text)
        height = self._default_font.metrics()['linespace']
        w_width, w_height = self.winfo_width(), self.winfo_height()

        # width is <=1 during startup
        if w_width <= 1:
            return self._current_font

        font = self._default_font.copy()
        font_size = self._default_font_size
        # decrease font size until it fits both width and height
        while width > w_width or height > w_height:
            font.config(size = font_size)
            # size 1 is the default when no size will fit
            if font_size == 1:
                break
            width = font.measure(text)
            height = font.metrics()['linespace']
            font_size -= 1
        self._current_font.config(size = font_size)

    @log_class
    def link(self, other):
        """ Link to another instance of FlexLabel so that their fonts change
        together. The font of self is taken from the linked instance other """
        if not isinstance(other, FlexLabel):
            raise ValueError("Linked object must be instance of FlexLabel")
        elif other == self:
            return
        # remove the fit_text binding
        self.unbind("<Configure>", self._fit_binding)
        self._link = other
        self._current_font = other._get_font()
        # use the same font object as the linked widget
        self.config(font = self._current_font)

class OptionList(tk.Toplevel):
    """ Window to get user input by selecting from a list of values. Optionally
    include a search bar at the top """
    @log_class
    def __init__(self, master, title = "Options", search = True, anchor = "w",
                 toplevel_kwargs = None, width = 300, height = 500,
                 *args, **kwargs):
        toplevel_kwargs = {} if toplevel_kwargs is None else toplevel_kwargs
        super().__init__(master, **toplevel_kwargs, width = width,
                         height = height)
        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

        self.window = futil.get_tk(self)
        self.include_search = search

        self.frame = base.TrimmedFrame(
            self, bg = c.COLOUR_BACKGROUND, width = width, height = height
            )
        self.frame.grid(row = 0, column = 0, **c.GRID_STICKY)

        if self.include_search:
            self.search_value = tk.StringVar()
            self.search_value.trace_add("write", self._write_value)
            self.search_box = ttk.Entry(
                self.frame.inner, justify = "left",
                textvariable = self.search_value
                )
            # if 'style' in kwargs:
            #     self.search_box.config(style = kwargs['style'])
            self.search_box.grid(row = 1, column = 0, **c.GRID_STICKY)

        self.table = dw.SimpleTreeview(
            self.frame.inner,
            colsdict = {1: {"header": title, "width": width,
                            "stretch": True, "anchor": anchor},}
            , *args, **kwargs
            )
        self.table.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.frame.inner.rowconfigure(1, weight = 1)

        self.value = None
        self.options = []
        self.table.bind("<Double-1>", self._set_value)

        self.bind("<Escape>", lambda event: self.destroy())
        self.table.bind("<Escape>", lambda event: self.destroy())
        self.bind("<Return>", self._enter)

    @log_class
    def set(self, options):
        """ Set the options, either as a list of values, or a dictionary of
        iid: text pairs """
        self.options = options
        self.load_options(options)

    @log_class
    def load_options(self, options):
        self.table.clear()
        if isinstance(options, list):
            for option in options:
                self.table.insert("", "end", iid = option, text = option)
        elif isinstance(options, dict):
            for iid, text in options.items():
                self.table.insert("", "end", iid = iid, text = text)
        else:
            raise ValueError("Options argument must be list of values or "
                             "dictionary of iid: text pairs")

    @log_class
    def get(self):
        return self.value

    @log_class
    def _enter(self, event = None):
        # set value as the first row
        self.value = self.table.get_children()[0]
        self.event_generate("<<SetValue>>")

    @log_class
    def _set_value(self, event):
        self.value = self.table.events["<Double-1>"]["row"]
        self.event_generate("<<SetValue>>")

    @log_class
    def start(self):
        self.window.eval(f'tk::PlaceWindow {self} center')
        self.overrideredirect(True)
        self.transient(self.master)
        self.grab_set()
        self.lift()

        if self.include_search:
            self.search_box.focus_force()
        else:
            self.table.focus_force()

        self.mainloop()

    @log_class
    def _write_value(self, *args):
         text = self.search_value.get()
         self.search(text)

    @log_class
    def search(self, text):
        options = self.options
        if isinstance(options, list):
            suboptions = [option for option in options
                          if self._matches(text, option)]
        elif isinstance(options, dict):
            suboptions = {iid: option for iid, option in options.items()
                          if self._matches(text, option)}
        self.load_options(suboptions)

    @staticmethod
    def _matches(text, option):
        return text.lower() in option.lower()

class RequestTitleWindow(tk.Toplevel):
    """ Window to get user film input, either as an IMDb ID or by searching for
    a film title """
    @log_class
    def __init__(self, master, type = "movie", *args, **kwargs):
        self.type = type
        super().__init__(master, *args, **kwargs)
        self.window = futil.get_tk(self)
        self.window.eval(f'tk::PlaceWindow {self} center')

        self.widget_frame = base.TrimmedFrame(
            self, bg = c.COLOUR_FILM_BACKGROUND,
            inner_colour = c.COLOUR_INTERFACE_BUTTON
            )
        self.widget_frame.grid(row = 0, column = 0, **c.GRID_STICKY)

        self.primary_search_frame = tk.Frame(
            self.widget_frame.inner, bg = c.COLOUR_FILM_BACKGROUND
            )
        title_type = {
            "movie": "film", "tv": "series", "episode": "episode"
            }[self.type]
        self.text = tk.Label(
            self.primary_search_frame, fg = c.COLOUR_OFFWHITE_TEXT,
            font = ("Helvetica", 24), bg = c.COLOUR_FILM_BACKGROUND,
            text = "Enter an IMDb ID or search for a %s title:" % title_type
            )
        self.text.bind("<Return>", self.search)

        self.search_trim = base.TrimmedFrame(self.primary_search_frame, height = 20)
        self.search_trim.outer.config(highlightthickness = 4)
        self.search_text = tk.Entry(
            self.search_trim.inner, width = 20, font = ("Helvetica", 16)
            )
        self.search_trim.columnconfigure(0, weight = 1)
        self.search_text.grid(row = 0, column = 0, **c.GRID_STICKY)

        self.btn_close = tk.Button(
            self.primary_search_frame, command = self.destroy,
            text = "Close", font = ("Helvetica", 24, )
            )
        self.btn_search = tk.Button(
            self.primary_search_frame, command = self.search,
            text = "Search", font = ("Helvetica", 24, )
            )

        widgets = {1: {'widget': self.text,
                       'grid_kwargs': {**c.GRID_STICKY, "padx": 15, "pady": 15},
                       'stretch_width': True},
                   2: {'widget': self.search_trim,
                       'grid_kwargs': {**c.GRID_STICKY, "pady": 5, "padx": 10},
                       'stretch_width': True},
                   3: {'widget': self.btn_close,
                       'grid_kwargs': {**c.GRID_STICKY, "pady": 5, "padx": 5}},
                   4: {'widget': self.btn_search,
                       'grid_kwargs': {**c.GRID_STICKY, "pady": 5, "padx": 5}},
                   -1: {'widget_kwargs': {"bg": c.COLOUR_FILM_BACKGROUND}}
                   }
        self.primary_search_set = tka.WidgetSet(
            self.primary_search_frame, widgets, [[1], [2], [3, 4]]
            )
        self.primary_search_frame.grid(row = 0, column = 0, **c.GRID_STICKY)

        # frame to hold the secondary search widgets to display search results
        self.secondary_search_frame = tk.Frame(
            self.widget_frame.inner, bg = c.COLOUR_FILM_BACKGROUND
            )
        self.search_results = dw.SimpleTreeview(
            self.secondary_search_frame,
            colsdict = {1: {"header": "", "width": 1,
                            "stretch": True, "anchor": "w"},
                        2: {"header": "Type", "width": 50,
                            "stretch": False, "anchor": "center"},
                        3: {"header": "Title", "width": 500,
                            "stretch": True, "anchor": "w"},}
            )
        self.search_results.bind("<Double-1>", self.select_search_result)
        self.search_results.grid(row = 0, column = 0, pady = (5, 15), padx = 10)
        self.secondary_search_frame.columnconfigure(0, weight = 1)
        self.secondary_search_frame.rowconfigure(0, weight = 1)

        self.search_text.focus_force()

        self.bind("<Escape>", lambda event: self.destroy())
        self.bind("<Return>", self.search)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    @log_class
    def destroy(self, *args):
        self.event_generate("<<Destroy>>")
        super().destroy()

    @log_class
    def search(self, *args, **kwargs):
        """ Called from btn_search """
        search_text = self.search_text.get().strip()
        if self.is_imdb_id(search_text):
            self.set_value(search_text)
        else:
            search_results = imdbf.search_title(search_text, type = self.type)
            self.load_search_results(search_results)
            self.add_secondary_search_widgets()

    @log_class
    def add_secondary_search_widgets(self):
        """ Display the search results widgets """
        self.secondary_search_frame.grid(row = 1, column = 0, **c.GRID_STICKY)

    @log_class
    def _search_results_values(self, res_dict):
        """ Get the value lists needed for the result treeview from the search
        results dict """
        episode = ("E%02d" % int(res_dict["episode"])
                   if res_dict["episode"] != "" else "")
        season = ("S%02d" % int(res_dict["season"])
                  if res_dict["season"] != "" else "")
        series_ending = (" (%s : %s%s)" % (res_dict["episode of"], season, episode)
                         if episode != "" else "")

        title = res_dict["title"] + series_ending + " (%s)" % res_dict["year"]
        return [res_dict["type"], title]

    @log_class
    def load_search_results(self, results):
        """ Load a dictionary of search results into the results treeview """
        self.search_results.clear()
        for i, result_dict in enumerate(results):
            self.search_results.insert(
                '', 'end', iid = result_dict["title_id"],
                values = self._search_results_values(result_dict)
                )

    @log_class
    def select_search_result(self, *args, **kwargs):
        """ Called when a search result is chosen """
        title_id = self.search_results.events["<Double-1>"]["row"]
        title_id = standardise_id(title_id)
        self.set_value(title_id)

    @log_class
    def is_imdb_id(self, text):
        """ Return bool, if text is formatted like an IMDb ID. This says
        nothing about if it is a *valid* ID or not. """
        # remove leading "tt"
        if text[0:2] == "tt":
            text = text[2:]
        # test for 7/8 digit number (imdb title ID)
        if re.match("\d{7,8}", text):
            return True
        else:
            return False

    @log_class
    def start(self):
        self.window.eval(f'tk::PlaceWindow {self} center')
        self.overrideredirect(True)
        self.transient(self.master)
        self.grab_set()
        self.lift()
        self.mainloop()

    @log_class
    def set_value(self, value):
        self.user_input = value
        self.event_generate("<<SetValue>>")

    @log_class
    def get_value(self):
        """ Return user input """
        return self.user_input


class PolygonProgressBar(tk.Toplevel):
    """ Window to get user film input, either as an IMDb ID or by searching for
    a film title """
    @log_class
    def __init__(self, master, maximum = 1, width = 400, height = 100,
                  style = None, *args, **kwargs):
        self.type = type
        self.value = tk.IntVar()
        self.maximum = maximum
        super().__init__(master, width = width, height = height, *args, **kwargs)
        self.window = futil.get_tk(self)
        self.window.eval(f'tk::PlaceWindow {self} center')

        self.frame = base.TrimmedFrame(self, bg = c.COLOUR_BACKGROUND,
                                        width = width, height = height)
        self.frame.inner.config(width = width, height = height)
        self.frame.grid(row = 0, column = 0, **c.GRID_STICKY)

        self.progress = ttk.Progressbar(
            self.frame.inner, maximum = maximum, length = width,
            variable = self.value, mode = 'determinate', orient = 'horizontal',
            )
        if not style is None:
            self.progress.config(style = style)
        self.progress.grid(row = 0, column = 0, **c.GRID_STICKY,
                            ipady = int(height/2 - 20))

        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

        self.style_used = "Horizontal.TProgressbar" if style is None else style
        self.style = ttk.Style()

    @log_class
    def start_indeterminate(self, *args):
        self.progress.config(mode = 'indeterminate', maximum = 10)
        self.progress.start(interval = 50)

    @log_class
    def stop_indeterminate(self, *args):
        self.progress.stop()
        self.progress.config(mode = 'determinate', maximum = self.maximum)
        self.value.set(0)

    @log_class
    def step(self, cnt):
        self.value.set(self.get() + cnt)
        if self.get() == self.maximum:
            self.after(500, self.destroy)
        else:
            completion = int(self.get()/self.maximum * 100)
            if completion >= 45:
                self.style.configure(self.style_used, foreground = "white")
            else:
                self.style.configure(self.style_used, foreground = "black")

            self.style.configure(self.style_used, text = f'{completion} %')

    @log_class
    def get(self):
        return self.value.get()

    @log_class
    def destroy(self, *args):
        self.event_generate("<<Destroy>>")
        super().destroy()

    @log_class
    def start(self):
        self.window.eval(f'tk::PlaceWindow {self} center')
        self.overrideredirect(True)
        self.grab_set()
        self.lift()
        self.mainloop()

class HoverIcon(tk.Label):
    """ Class for images with a standard and hover state """
    def __init__(self, master, standard, hover = None, **kwargs):
        if "image" in kwargs:
            raise ValueError("Image argument should be set through the "
                             "'standard' keyword")
        kwargs.setdefault("cursor", "hand2")
        self.enable_hover = not hover is None
        self.image_standard = standard
        self.image_hover = hover
        super().__init__(master, **kwargs, image = self.image_standard)

        if self.enable_hover:
            self.bind("<Enter>", self._enter)
            self.bind("<Leave>", self._leave)

    def _enter(self, *args):
        self.config(image = self.image_hover)

    def _leave(self, *args):
        self.config(image = self.image_standard)

class HoverIconPath(HoverIcon):
    def __init__(self, master, standard, dimensions = None, hover = None,
                 **kwargs):
        super().__init__(
            master, standard = self.get_image(standard, dimensions),
            hover = self.get_image(hover, dimensions), **kwargs
            )

    def get_image(self, path, dimensions = None):
        if path is None:
            return
        with Image.open(path) as image:
            if not dimensions is None:
                image = image.resize(dimensions)
            return ImageTk.PhotoImage(image)

class HoverIconTick(HoverIcon):
    def __init__(self, master, height, **kwargs):
        super().__init__(
            master,
            standard = ImageTk.PhotoImage(
                tagf.tick_image(height = height, colour = "black")),
            hover = ImageTk.PhotoImage(
                tagf.tick_image(height = height, colour = "gray")),
            **kwargs)

class HoverIconCross(HoverIcon):
    def __init__(self, master, height, **kwargs):
        super().__init__(
            master,
            standard = ImageTk.PhotoImage(
                tagf.x_image(height = height, colour = "black")),
            hover = ImageTk.PhotoImage(
                tagf.x_image(height = height, colour = "gray")),
            **kwargs)

class HoverIconTag(HoverIcon):
    def __init__(self, master, value, height, **kwargs):
        super().__init__(
            master,
            standard = ImageTk.PhotoImage(
                image = tagf.text_tag(value, height = height)),
            hover = ImageTk.PhotoImage(
                image = tagf.text_tag(value, height = height,
                                      x_colour = "gray")),
            **kwargs)

# test = "RatingDisplay"
test = "TitleModule"
# test = "FlexLabel"

if __name__ == "__main__":
    root = tk.Tk()

    if test == "RatingDisplay":
        rating_frame = tk.Frame(root, bg = "white")
        # place ratings in frame to centre it vertically
        ratings = RatingDisplay(rating_frame, min_rating = 0, max_rating = 10,
                                font = ("Helvetica", 32, "bold"), bg = "white")
        ratings.set_colour_map(
            {1: "red", 2: "red", 3: "orange", 4: "orange", 5: "#ffbf00",
              6: "#ffbf00", 7: "lime green", 8: "lime green", 9: "forest green",
              10: "midnight blue"}
            )
        ratings.set(0)
        def rating_up():
            try: ratings.set(ratings.rating + 1)
            except ValueError: pass
        def rating_down():
            try: ratings.set(ratings.rating - 1)
            except ValueError: pass
        btn_up = tk.Button(root, text = "+", command = rating_up,
                           font = ("Helvetica", 32, "bold"))
        btn_down = tk.Button(root, text = "-", command = rating_down,
                             font = ("Helvetica", 32, "bold"))
        btn_up.grid(row = 0, column = 0, sticky = "nesw")
        btn_down.grid(row = 0, column = 2, sticky = "nesw")

        ratings.grid(row = 0, column = 0, sticky = "ew") #expand only sideways
        rating_frame.rowconfigure(0, weight = 1)
        rating_frame.columnconfigure(0, weight = 1)
        rating_frame.grid(row = 0, column = 1, sticky = "nesw")

        root.rowconfigure(0, weight = 1)
        root.columnconfigure(0, weight = 1)
        root.columnconfigure(1, weight = 1)
        root.columnconfigure(2, weight = 1)

    elif test == "TitleModule":
        title = TitleModule(root, bg = "black", pady = 30)
        title.set_text(
            date = "2022-01-22", title = "The Last Duel",
            director = "Ridley Scott", original_title = "The Last Duel",
            year = 2021, runtime = "156", rating = 4.5, rewatch = True,
            number = 1
            )
        title.grid(row = 0, column = 0, sticky = "nesw")

        for y in range(5):
            title = TitleModuleDetailed(root, bg = "black", pady = 30)
            title.set_text(
                date = "2022-01-22", title = "Those Magnificent Men in Their Flying Machines or How I Flew from London to Paris in 25 hours 11 minutes",
                director = "director", original_title = "abcdefghijklmnopqrstuvwxyz",
                year = 2021, runtime = "165", rating = 10, rewatch = False,
                number = 2, plot_tag = "Hoping to push Britain to the forefront of aviation, a London publisher organizes an international air race across the English Channel, but must contend with two entrants vying for his daughter, as well as national rivalries and cheating.",
                tags = imdbf.get_tags('tt2953050')
                )
            title.grid(row = y, column = 0, sticky = "nesw")
        root.bind("<Return>", title.replace_tag_widgets)
        root.rowconfigure(0, weight = 1)
        root.rowconfigure(1, weight = 1)
        root.columnconfigure(0, weight = 1)

    elif test == "FlexLabel":
        title = FlexLabel(root, text = "this is some test text", font = ("Arial", 45, "bold"))
        title.grid(row = 0, column = 0, sticky = "nesw")

        title2 = FlexLabel(root, text = "this is short txt")
        title2.link(title)
        title2.grid(row = 1, column = 0, sticky = "nesw")

        root.rowconfigure(0, weight = 1)
        root.rowconfigure(1, weight = 1)
        root.columnconfigure(0, weight = 1)

    root.mainloop()
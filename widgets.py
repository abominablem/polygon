# -*- coding: utf-8 -*-
"""
Created on Sun Jan 23 21:02:39 2022

@author: marcu
"""

import tkinter as tk
import tkinter.font as tkf
from datetime import datetime

import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import tk_arrange as tka
from mh_logging import log_class
import constants as c
import futil as futil
import base
import math

log_class = log_class(c.LOG_LEVEL)

class RatingDisplay(tk.Text):
    """ Display a rating out of N stars """
    @log_class
    def __init__(self, master, min_rating = 1, max_rating = 10, **kwargs):

        self.set_symbol(empty_symbol = "☆", filled_symbol = "★")
        self.set_colour(empty_colour = "#D3D3D3", filled_colour = "black")
        self.set_colour_map({})

        self.min_rating = min_rating
        self.max_rating = max_rating
        self.rating = 1
        self._capture_kwarg(kwargs, "empty_symbol", "_symbol_empty")
        self._capture_kwarg(kwargs, "filled_symbol", "_symbol_filled")
        self._capture_kwarg(kwargs, "empty_colour", "_colour_empty")
        self._capture_kwarg(kwargs, "filled_colour", "_colour_filled")
        self._capture_kwarg(kwargs, "colour_map", "colour_map")

        kwargs = self._remove_kwargs(kwargs, [
            "empty_symbol", "filled_symbol", "empty_colour", "filled_colour",
            "colour_map"
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
    def set_symbol(self, empty_symbol = None, filled_symbol = None):
        """ Set the symbols for filled and empty rating symbols """
        if not empty_symbol is None: self._symbol_empty = empty_symbol
        if not filled_symbol is None: self._symbol_filled = filled_symbol

    @log_class
    def set_colour(self, empty_colour = None, filled_colour = None):
        """ Set the colours of filled and empty rating symbols """
        if not empty_colour is None: self._colour_empty = empty_colour
        if not filled_colour is None: self._colour_filled = filled_colour

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
            else:
                col_def = {"filled_colour": col_def,
                           "empty_colour": self._colour_empty}
            colour_map[rating] = col_def
        self.colour_map = colour_map

    @log_class
    def _set_colour_tags(self):
        """ Colour the text according to rules defined so far """
        colfill = self.colour_map.get(self.rating, {}).get(
            "filled_colour", self._colour_filled)
        colempty = self.colour_map.get(self.rating, {}).get(
            "empty_colour", self._colour_empty)
        self.tag_config("filled_rating", foreground = colfill)
        self.tag_config("empty_rating", foreground = colempty)

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
        self.insert("end", self._symbol_filled * rating,
                    ["filled_rating", 'center'])
        self.insert("end", self._symbol_empty * (self.max_rating - rating),
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
        x, y = event.x, event.y
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

class TitleModule(tk.Frame):
    """ Bordered frame containing Date, Title, Original title, Director, Year,
    Runtime, and Rating """
    @log_class
    def __init__(self, master, include_rewatch = True, include_number = True,
                 **kwargs):
        self.master = master
        super().__init__(self.master, **kwargs)

        font_date = ("Calibri", 28, "bold")
        font_title = ("Calibri", 32)
        font_subtitle = ("Calibri", 22, "italic")
        font_rating = ("Calibri", 36, "bold")
        font_rewatch = ("Calibri", 36)
        font_number = ("Calibri", 36)

        self.border_frame = base.TrimmedFrame(self)
        self.border_frame.columnconfigure(0, weight = 1)

        self.widget_frame = tk.Frame(self.border_frame.inner)
        self.date = tk.Label(
            self.widget_frame, bg = "white", anchor = "center",
            font = font_date, padx = 20, pady = 0, width = 10
            )
        self.title = tk.Label(
            self.widget_frame, bg = "white", anchor = "w", font = font_title,
            padx = 10, pady = 0, width = 40
            )
        self.original_title = tk.Label(
            self.widget_frame, bg = "white", anchor = "w",
            font = font_subtitle, padx = 10, pady = 0
            )
        self._original_title_text = ""
        self.director = tk.Label(
            self.widget_frame, bg = "white", anchor = "e",
            font = font_subtitle, padx = 10, pady = 0
            )
        self.year = tk.Label(
            self.widget_frame, bg = "white", anchor = "center",
            font = font_title, padx = 20, pady = 0
            )
        self.runtime = tk.Label(
            self.widget_frame, bg = "white", anchor = "center",
            font = font_subtitle, padx = 20, pady = 0
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
            self.widget_frame, widgets, layout = [[1, 2, 2, 5],
                                                  [1, 3, 4, 6]])
        self.widget_frame.grid(row = 0, column = 0, **c.GRID_STICKY)

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
    def format_runtime(self, runtime):
        try:
            return futil.format_time(int(runtime), "minutes")
        except ValueError:
            return "N/A"

    @log_class
    def format_date(self, date):
        return datetime.strptime(date, "%Y-%m-%d").strftime("%d %b %Y")

    @log_class
    def get_dict(self):
        return self._value_dict

    @log_class
    def set_text(self, **kwargs):
        self._value_dict.update(kwargs)
        for kw in kwargs:
            if kw == "rating":
                self.rating.set(int(kwargs[kw]))

            elif kw == "runtime":
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

            elif kw == "rewatch" and self.include_rewatch:
                if kwargs[kw]:
                    self.rewatch.config(fg = "white")
                else:
                    self.rewatch.config(fg = c.COLOUR_FILM_BACKGROUND)

            elif kw == "number" and self.include_number:
                self.__dict__[kw].config(text = kwargs[kw])

            else:
                self.__dict__[kw].config(text = kwargs[kw])

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
        self._default_font = self._get_font_object(_font_argument)
        self._default_font_size = self._default_font.cget('size')

        self.bind("<Configure>", self._fit_text)

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
        text = self.cget('text')
        self.config(font = self._get_font(text))

    @log_class
    def _get_font(self, text):
        """ Get the font needed to fit the given text into the widget """
        width = self._default_font.measure(text)
        w_width, w_height = self.winfo_width(), self.winfo_height()

        # width is <=1 during startup
        if w_width <= 1: return self.font_count

        font = self._default_font.copy()
        font_size = self._default_font_size
        # decrease font size until it fits both width and height
        while width > w_width or font.metrics()['linespace'] > w_height:
            font.config(size = font_size)
            # size 1 is the smallest possible font, so use as default in the
            # case that no size font will fit in the available space
            if font_size == 1: return font
            width = font.measure(text)
            font_size -= 1
        return font


# test = "RatingDisplay"
# test = "TitleModule"
test = "FlexLabel"

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
            year = 2021, runtime = "156", rating = 6, rewatch = True,
            number = 1
            )
        title.grid(row = 0, column = 0, sticky = "nesw")
        title = TitleModule(root, bg = "black", pady = 30)
        title.set_text(
            date = "2022-01-22", title = "Those Magnificent Men in Their Flying Machines or How I Flew from London to Paris in 25 hours 11 minutes",
            director = "director", original_title = "abcdefghijklmnopqrstuvwxyz",
            year = 2021, runtime = "165", rating = 10, rewatch = False,
            number = 2
            )
        title.grid(row = 1, column = 0, sticky = "nesw")
        root.rowconfigure(0, weight = 1)
        root.rowconfigure(1, weight = 1)
        root.columnconfigure(0, weight = 1)

    elif test == "FlexLabel":
        title = FlexLabel(root, text = "this is some test text", font = ("Arial", 45, "bold"))
        title.grid(row = 0, column = 0, sticky = "nesw")
        root.rowconfigure(0, weight = 1)
        root.columnconfigure(0, weight = 1)

    root.mainloop()
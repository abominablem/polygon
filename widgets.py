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
        "filled_colour". "empty_colour" will revert to the default. """

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
        colfill = self.colour_map.get(self.rating, {}).get("filled_colour", self._colour_filled)
        colempty = self.colour_map.get(self.rating, {}).get("empty_colour", self._colour_empty)
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
        self.insert("end", self._symbol_filled * rating, ["filled_rating", 'center'])
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


class TitleModule(tk.Frame):
    """ Bordered frame containing Date, Title, Original title, Director, Year,
    Runtime, and Rating """
    @log_class
    def __init__(self, master, include_rewatch = True, include_number = True,
                 **kwargs):
        self.master = master
        super().__init__(self.master, **kwargs)
        font_date = ("Calibri", 24, "bold")
        font_title = ("Calibri", 28)
        font_subtitle = ("Calibri", 18, "italic")
        font_rating = ("Calibri", 32, "bold")
        font_number = ("Calibri", 32)

        self.border_frame = tk.Frame(
            self, highlightthickness = 7, highlightbackground = "lime green",
            highlightcolor = "lime green"
            )

        self.widget_frame = tk.Frame(self.border_frame)
        self.date = tk.Label(
            self.widget_frame, bg = "white", anchor = "center",
            font = font_date, padx = 20, pady = 0
            )
        self.title = tk.Label(
            self.widget_frame, bg = "white", anchor = "w", font = font_title,
            padx = 10, width = 40, pady = 0
            )
        self.original_title = tk.Label(
            self.widget_frame, bg = "white", anchor = "w", font = font_subtitle,
            padx = 10, pady = 0
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
                       'stretch_width': True, 'stretch_width_weight': 3},
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

        self.rating_frame = tk.Frame(self.border_frame)
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


        self.include_number = include_number
        if include_number:
            self.number = tk.Label(
                self, bg = "black", anchor = "center", font = font_number,
                padx = 40, fg = "white"
                )
            self.number.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.border_frame.grid(row = 0, column = 1, **c.GRID_STICKY)

        self.include_rewatch = include_rewatch
        if include_rewatch:
            self.rewatch = tk.Label(
                self, bg = "black", anchor = "center", font = font_rating,
                padx = 40, fg = "white"
                )
            self.rewatch.grid(row = 0, column = 2, **c.GRID_STICKY)

        self.border_frame.columnconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

    @log_class
    def format_runtime(self, runtime):
        return futil.format_time(int(runtime), "minutes")

    @log_class
    def format_date(self, date):
        return datetime.strptime(date, "%Y-%m-%d").strftime("%d %b %Y")

    @log_class
    def set_text(self, **kwargs):
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
                text = kwargs[kw]
                self.date.config(text = self.format_date(text))

            elif kw == "rewatch" and self.include_rewatch:
                if kwargs[kw]:
                    self.rewatch.config(text = "⟳")
                else:
                    self.rewatch.config(text = "")

            else:
                self.__dict__[kw].config(text = kwargs[kw])



# test = "RatingDisplay"
test = "TitleModule"

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
        title = TitleModule(root)
        title.set_text(date = "2022-01-22", title = "The Last Duel",
                      director = "Ridley Scott",
                      original_title = "The Last Duel",
                      year = 2021, runtime = "156", rating = 6,
                      rewatch = True, number = 1)
        title.grid(row = 0, column = 0, sticky = "nesw")
        root.rowconfigure(0, weight = 1)
        root.columnconfigure(0, weight = 1)

    root.mainloop()
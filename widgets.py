# -*- coding: utf-8 -*-
"""
Created on Sun Jan 23 21:02:39 2022

@author: marcu
"""

import tkinter as tk
import tkinter.font as tkf


class RatingDisplay(tk.Text):
    """ Display a rating out of N stars """
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
                         state = 'disabled')

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

    def get_width(self):
        """ Get the width of the text widget based on the maximum
        font_measure'd width of the symbols and max rating. For use when
        placing the widget in the geometry """
        widths = [self.font.measure(self._symbol_empty * self.max_rating),
                  self.font.measure(self._symbol_filled * self.max_rating)]
        return max(widths)

    def refresh(self):
        self.set(self.rating)

    def set_symbol(self, empty_symbol = None, filled_symbol = None):
        """ Set the symbols for filled and empty rating symbols """
        if not empty_symbol is None: self._symbol_empty = empty_symbol
        if not filled_symbol is None: self._symbol_filled = filled_symbol

    def set_colour(self, empty_colour = None, filled_colour = None):
        """ Set the colours of filled and empty rating symbols """
        if not empty_colour is None: self._colour_empty = empty_colour
        if not filled_colour is None: self._colour_filled = filled_colour

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

    def _set_colour_tags(self):
        """ Colour the text according to rules defined so far """
        colfill = self.colour_map.get(self.rating, {}).get("filled_colour", self._colour_filled)
        colempty = self.colour_map.get(self.rating, {}).get("empty_colour", self._colour_empty)
        self.tag_config("filled_rating", foreground = colfill)
        self.tag_config("empty_rating", foreground = colempty)

    def _clear(self):
        """ Clear the text widget """
        self.configure(state='normal')
        self.delete(1.0, tk.END)
        self.configure(state='disabled')

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

    def _capture_kwarg(self, dict, kw, attr):
        """ Update the attribute attr with the value in dict[kw] """
        if kw in dict:
            self.__dict__[attr] = dict[kw]

    def _remove_kwargs(self, dict, kws):
        """ Remove keys in list from dict if they exist """
        for kw in kws:
            if kw in dict: del dict[kw]
        return dict

if __name__ == "__main__":
    root = tk.Tk()

    rating_frame = tk.Frame(root)
    # place ratings in frame to centre it vertically
    ratings = RatingDisplay(rating_frame, min_rating = 0, max_rating = 10,
                            font = ("Helvetica", 32, "bold"))
    ratings.set_colour_map(
        {1: "red", 2: "red", 3: "orange", 4: "orange", 5: "#ffbf00", 6: "#ffbf00",
         7: "lime green", 8: "lime green", 9: "forest green", 10: "midnight blue"}
        )

    ratings.set(0)

    def rating_up():
        try: ratings.set(ratings.rating + 1)
        except ValueError: pass
    def rating_down():
        try: ratings.set(ratings.rating - 1)
        except ValueError: pass
    btn_up = tk.Button(root, text = "+", command = rating_up, font = ("Helvetica", 32, "bold"))
    btn_down = tk.Button(root, text = "-", command = rating_down, font = ("Helvetica", 32, "bold"))
    btn_up.grid(row = 0, column = 0, sticky = "nesw")
    btn_down.grid(row = 0, column = 2, sticky = "nesw")

    ratings.grid(row = 0, column = 0, sticky = "ew")
    rating_frame.rowconfigure(0, weight = 1)
    rating_frame.columnconfigure(0, weight = 1)
    rating_frame.grid(row = 0, column = 1, sticky = "nesw")

    root.rowconfigure(0, weight = 1)
    root.columnconfigure(0, weight = 1)
    root.columnconfigure(1, weight = 1)
    root.columnconfigure(2, weight = 1)

    root.mainloop()
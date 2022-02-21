# -*- coding: utf-8 -*-
"""
Created on Wed Jan  5 21:31:00 2022

@author: marcu
"""
import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import tkinter as tk
from tkinter import ttk

from mh_logging import log_class
import tk_arrange as tka
import constants as c

import base
from film_tracker import FilmTracker
from tv_tracker import TvTracker

log_class = log_class(c.LOG_LEVEL)

class Polygon(tk.Tk):
    @log_class
    def __init__(self):
        super().__init__()
        self.title("Polygon")
        self.iconphoto(True, tk.PhotoImage(file = c.LOGO_PATH))
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.columnconfigure(0, weight = 1)
        self.rowconfigure(0, weight = 1)
        self.style(self)

        self.widget_frame = tk.Frame(self, bg = c.COLOUR_BACKGROUND)
        self.header = base.PolygonFrameBase(self.widget_frame)

        self.divider = tk.Frame(self.widget_frame, bg = "white", height = 1)

        self.film_tracker = FilmTracker(
            self.widget_frame, bg = c.COLOUR_FILM_BACKGROUND
            )
        self.tv_tracker = TvTracker(
            self.widget_frame, bg = c.COLOUR_FILM_BACKGROUND
            )

        widgets = {1: {'widget': self.header,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True},
                   2: {'widget': self.divider,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True, 'stretch_height': False},
                   3: {'widget': self.film_tracker,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True, 'stretch_height': True},
                   }
        self.widget_set = tka.WidgetSet(
            self.widget_frame, widgets, layout = [[1], [2], [3]])

        self.widget_set.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.launch_module("film")

    @log_class
    def launch_module(self, module):
        widget = {"film": self.film_tracker, "tv": self.tv_tracker}[module]
        widget.grid(**self.widget_set._get_grid_refs(3), **c.GRID_STICKY)

    @log_class
    def destroy(self, event = None):
        self.running = False
        self.quit()
        super().destroy()
        base.polygon_db.close()

    @log_class
    def start(self):
        self.eval('tk::PlaceWindow . center')
        self.mainloop()

    @log_class
    def style(self, master):
        style = ttk.Style(master)

        style.layout('TNotebook.Tab', False)
        " TV Tracker - Episode Table "
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



polygon = Polygon()
polygon.start()
base.polygon_db.close()
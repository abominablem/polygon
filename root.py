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
        self._style(self)

        self.widget_frame = tk.Frame(self, bg = c.COLOUR_TITLEBAR)
        self.header = base.PolygonFrameBase(self.widget_frame)
        self.icons = base.IconSet(self.widget_frame, bg = c.COLOUR_TITLEBAR)
        self.icons.rowconfigure(0, weight = 1)
        icon_kwargs = dict(
            bg = c.COLOUR_TITLEBAR, font = ("Calibri", 50),
            padx = 20, anchor = "center", fg = c.COLOUR_TITLEBAR_ICON,
            cursor = "hand2", hover = c.COLOUR_TITLEBAR_ICON_HOVER,
            select = c.COLOUR_TITLEBAR_ICON_SELECTED
            )
        self.icons.add(text = "📺", name = "tv", **icon_kwargs)
        self.icons.add(text = "🎞", name = "film", **icon_kwargs)
        for name in ["film", "tv"]:
            self.icons[name].bind(
                "<1>", lambda event: self.launch_module(event.widget.name),
                add = "+"
                )

        self.divider = tk.Frame(self.widget_frame, bg = "white", height = 1)

        self.film_tracker = FilmTracker(
            self.widget_frame, bg = c.COLOUR_FILM_BACKGROUND
            )
        self.tv_tracker = TvTracker(
            self.widget_frame, bg = c.COLOUR_FILM_BACKGROUND
            )

        self.icons["film"].bind(
            "<1>", lambda event: self.film_tracker.set_titlemod_mode("entries")
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
                   4: {'widget': self.icons,
                       'grid_kwargs': {**c.GRID_STICKY, "padx": (0, 30)}},
                   }
        self.widget_set = tka.WidgetSet(
            self.widget_frame, widgets, layout = [[1, 4], [2], [3]])

        self.widget_set.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.launch_module("film")

    @log_class
    def launch_module(self, module):
        widgets = {"film": self.film_tracker, "tv": self.tv_tracker}

        widget = widgets[module]
        for name, wdgt in widgets.items():
            if name != module:
                wdgt.grid_forget()
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
    def _style(self, master):
        self.style = ttk.Style(master)

        " TV Tracker - Episode Table "
        self.style.configure(
            "EpisodeTable.Treeview", fieldbackground="white",
            font = ('Calibri', 20), rowheight = 40, relief = 'flat'
            )
        self.style.map(
            'EpisodeTable.Treeview', background=[('selected', '#F5F5F5')],
            foreground=[('selected', 'black')]
            )
        self.style.configure(
            "EpisodeTable.Treeview.Heading", font = ('Calibri', 20,'bold'),
            padding = 5, rowheight = 60
            )

        self.style.configure(
            "SeriesList.Treeview.Heading", font = ('Calibri', 15,'bold'),
            padding = 5, rowheight = 30
            )
        self.style.configure(
            "SeriesList.Treeview", font = ('Calibri', 12),
            padding = 5, rowheight = 20
            )

        " TV Tracker - DownloadData Table "
        self.style.configure(
            "DownloadData.Treeview", fieldbackground="white",
            font = ('Calibri', 20), rowheight = 40, relief = 'flat'
            )
        self.style.map(
            'DownloadData.Treeview',
            background=[('selected', 'midnight blue')],
            foreground=[('selected', 'white')]
            )
        self.style.configure(
            "DownloadData.Treeview.Heading", font = ('Calibri', 20,'bold'),
            padding = 5, rowheight = 60
            )

        self.style.layout(
            'PolygonProgress.Horizontal.TProgressbar',
            [('Horizontal.Progressbar.trough',
              {'children': [('Horizontal.Progressbar.pbar',
                              {'side': 'left', 'sticky': 'ns'})],
                'sticky': 'nswe'}),
              ('Horizontal.Progressbar.label', {'sticky': ''})])
        self.style.configure(
            "PolygonProgress.Horizontal.TProgressbar",
            foreground = "black", background = "midnight blue",
            bordercolor = "midnight blue", lightcolor = "midnight blue",
            darkcolor = "midnight blue", text = '0%',
            font = ('Calibri', 15, 'bold')
            )


polygon = Polygon()
polygon.start()
base.polygon_db.close()
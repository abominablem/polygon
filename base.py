# -*- coding: utf-8 -*-
"""
Created on Thu Jan  6 20:24:28 2022

@author: marcu
"""
import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import tkinter as tk
from PIL import Image, ImageTk

from mh_logging import log_class
import tk_arrange as tka
from PIL_util import pad_image_with_transparency
from sqlite_tablecon import TableCon, MultiConnection
import constants as c

log_class = log_class(c.LOG_LEVEL)

class PolygonFrameBase:
    """ Base tk.Frame with menu, Polygon logo, and title bar """
    @log_class
    def __init__(self, master, title = "Polygon"):
        self.master = master
        self.widget_frame = tk.Frame(self.master, bg = c.COLOUR_BACKGROUND)
        """ Draw logo"""
        with Image.open(".\common\logo.png") as image:
            self.img_logo = ImageTk.PhotoImage(image.resize((145, 145)))
            self.img_logo_padded = ImageTk.PhotoImage(
                pad_image_with_transparency(
                    image.resize((130, 130)), 15, keep_size = True
                    )
                )
        self.title = tk.Label(
            self.widget_frame,
            text = title,
            background = c.COLOUR_TITLEBAR,
            foreground = c.COLOUR_OFFWHITE_TEXT,
            padx = 20,
            font = c.FONT_MAIN_TITLE,
            anchor = "w",
            )
        self.logo = tk.Label(
            self.widget_frame,
            image = self.img_logo_padded,
            background = c.COLOUR_TITLEBAR,
            anchor = "w", padx = 20,
            )

        widgets = {1: {'widget': self.logo,
                       'grid_kwargs': c.GRID_STICKY},
                   2: {'widget': self.title,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True},
                   }
        self.widget_set = tka.WidgetSet(
            self.widget_frame, widgets, layout = [1, 2])

        self.widget_set.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.master.rowconfigure(0, weight = 1)
        self.master.columnconfigure(0, weight = 1)

    @log_class
    def get_widget(self):
        return self.widget_set

    @log_class
    def grid(self, **kwargs):
        self.widget_set.grid(**kwargs)

    def rowconfigure(self, *args, **kwargs):
        self.widget_set.rowconfigure(*args, **kwargs)

    def columnconfigure(self, *args, **kwargs):
        self.widget_set.columnconfigure(*args, **kwargs)

class PolygonWindowBase:
    """ Toplevel window with OctaveFrameBase """
    @log_class
    def __init__(self, master, title = "Octave"):
        self.master = master
        self.window = tk.Toplevel(self.master, bg = c.COLOUR_BACKGROUND)
        self.master.eval(f'tk::PlaceWindow {self.window} center')
        self.title_bar = PolygonFrameBase(self.window, title = title)

    @log_class
    def start(self):
        # self.window.transient(self.master)
        self.window.grab_set()
        self.window.mainloop()

class PolygonConnections:
    def __init__(self, db, tables = None):
        self.db = db
        if tables is None:
            raise AttributeError("At least one table must be specified")
        elif not isinstance(tables, list):
            tables = [tables]

        for table in tables:
            self.__dict__[table] = TableCon(db = db, table = table,
                                            debug = c.DEBUG)

polygon_db = MultiConnection(
    r".\data\polygon.db",
    ["series", "episodes", "titles", "entries", "tags"]
    )

# polygon_db.execute("CREATE TABLE series(series_id text not null, name text not null, custom_name text, genres text, notes text, imdb_user_rating double, imdb_user_votes int, rating int, import_date date)")
# polygon_db.execute("CREATE TABLE episodes(title_id text not null, series_id text not null, season int not null, episode int not null,  foreign key (series_id) references series (series_id),  foreign key (title_id) references titles (title_id))")
# polygon_db.execute("CREATE TABLE titles(title_id text not null, type text not null, title text not null, original_title text, custom_title text, release_date date, year int, director text, genre text, runtime int, imdb_user_rating double, imdb_user_votes int, import_date date)")
# polygon_db.execute("CREATE TABLE entries(entry_id integer primary key autoincrement, title_id text not null, entry_date date, entry_order int not null, rewatch bool, notes text,  foreign key (title_id) references titles (title_id))")
# polygon_db.execute("CREATE TABLE tags(entry_id int, tag_name text, tag_value text not null,  foreign key (entry_id) references entries (entry_id))")

if __name__ == "__main__":
    class TestApp:
        @log_class
        def __init__(self):
            self.root = tk.Tk()
            btn_start_rec = tk.Button(
                self.root, text = "btn1",
                command = self.start_window,
                font = ("Constantia", 32, "bold"))
            btn_start_rec.grid(row = 1, column = 0)

            self.root.mainloop()

        @log_class
        def start_window(self):
            title_bar = PolygonWindowBase(self.root, title = "TEST WINDOW")
            btn_stop_rec = tk.Button(
                title_bar.window, text = "btn2",
                font = ("Constantia", 32, "bold"))
            btn_stop_rec.grid(row = 1, column = 0)
            title_bar.start()

    app = TestApp()
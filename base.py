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
from sqlite_tablecon import MultiConnection
import constants as c

log_class = log_class(c.LOG_LEVEL)

class PolygonException(Exception):
    pass

class PolygonFrameBase:
    """ Base tk.Frame with menu, Polygon logo, and title bar """
    @log_class
    def __init__(self, master, title = "Polygon"):
        self.master = master
        self.widget_frame = tk.Frame(self.master, bg = c.COLOUR_BACKGROUND)
        """ Draw logo"""
        with Image.open(c.LOGO_PATH) as image:
            self.img_logo = ImageTk.PhotoImage(image.resize((145, 145)))
            self.img_logo_padded = ImageTk.PhotoImage(
                pad_image_with_transparency(
                    image.resize((130, 130)), 15, keep_size = True
                    )
                )
        self.title = tk.Label(
            self.widget_frame, text = title, background = c.COLOUR_TITLEBAR,
            foreground = c.COLOUR_OFFWHITE_TEXT, padx = 20, anchor = "w",
            font = c.FONT_MAIN_TITLE,
            )
        self.logo = tk.Label(
            self.widget_frame, image = self.img_logo_padded,
            background = c.COLOUR_TITLEBAR, anchor = "w", padx = 20,
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

class PolygonWindowBase(tk.Toplevel):
    """ Toplevel window with OctaveFrameBase """
    @log_class
    def __init__(self, master, title = "Octave", **kwargs):
        super().__init__(master, bg = c.COLOUR_BACKGROUND, **kwargs)
        self.master.eval(f'tk::PlaceWindow {self} center')
        self.title_bar = PolygonFrameBase(self, title = title)

    @log_class
    def start(self):
        self.grab_set()
        self.mainloop()

class IconSet(tk.Frame):
    @log_class
    def __init__(self, *args, **kwargs):
        self.icons = {}
        self._icon_colours = {}
        super().__init__(*args, **kwargs)

    @log_class
    def add(self, text, name = None, stretch = False, hover = None,
            select = None, **kwargs):
        """
        Add a new icon to the right of the set

        Parameters
        ----------
        text : str
            Text to display on icon
        name : str, optional
            Friendly name to refer to the icon widget in the backend.
            The default is the text argument.
        stretch : bool, optional
            Stretch the icon horizontally or not?. The default is False.
        hover : colour, optional
            Colour of the icon when hovering over it with the mouse. The
            default is None.
        select : colour, optional
            Colour of the icon when it is the last one clicked. The
            default is None.
        **kwargs : *
            widget kwargs for the Label.

        Returns
        -------
        icon : tk.Label
        """
        if name is None:
            name = text

        icon = tk.Label(self, text = text, **kwargs)
        column = len(self.icons)

        if stretch:
            self.columnconfigure(column, weight = 1)

        icon.grid(row = 0, column = len(self.icons), **c.GRID_STICKY)
        icon.name = name
        fg = icon.cget('fg')

        self._icon_colours[name] = {'fg': fg, 'current': fg}

        # update the foreground colour when hovering over the icon
        if not hover is None:
            self._icon_colours[name]['hover'] = hover
            def enter_func(event):
                w = event.widget
                self._icon_colours[w.name]["current"] = w.cget('fg')
                w.config(fg = self._icon_colours[w.name]["hover"])

            def leave_func(event):
                w = event.widget
                w.config(fg = self._icon_colours[w.name]["current"])

            icon.bind("<Enter>", enter_func)
            icon.bind("<Leave>", leave_func)

        # update the foreground colour when the icon is the last one clicked
        if not select is None:
            self._icon_colours[name]['select'] = select
            def click_func(event):
                print("click")
                w = event.widget
                for icon in self.icons:
                    if icon != w.name:
                        self[icon].config(fg = self._icon_colours[icon]['fg'])
                col = self._icon_colours[w.name]["select"]
                self._icon_colours[w.name]["current"] = col
                w.config(fg = col)

            icon.bind("<1>", click_func)

        self.icons[name] = icon
        return icon

    def __getitem__(self, name):
        return self.icons[name]

class TrimmedFrame(tk.Frame):
    @log_class
    def __init__(self, master, outer_colour = c.COLOUR_FILM_TRIM,
                 inner_colour = "black", *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.inner_colour = inner_colour
        self.outer_colour = outer_colour

        self.outer = tk.Frame(
            self, highlightthickness = 7,
            highlightbackground = outer_colour,
            highlightcolor = outer_colour
            )
        self.inner = tk.Frame(
            self.outer, highlightthickness = 1,
            highlightbackground = inner_colour, highlightcolor = inner_colour
            )
        self.outer.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.outer.columnconfigure(0, weight = 1)
        self.outer.rowconfigure(0, weight = 1)
        self.inner.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.inner.columnconfigure(0, weight = 1)
        self.inner.rowconfigure(0, weight = 1)

polygon_db = MultiConnection(
    r".\data\polygon.db",
    ["series", "episodes", "titles", "entries", "entry_tags", "title_tags"],
    debug = c.DEBUG
    )

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
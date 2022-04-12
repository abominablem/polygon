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

from datetime import datetime

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

class WidgetCollection(tk.Frame):
    """ Organised collection of a dynamic set of widget instances """
    @log_class
    def __init__(self, master, unit_widget, minmax = None, wkwargs = None,
                 orientation = "vertical", expand = "both", **kwargs):

        self.set_minmax(minmax)
        if not orientation in ["vertical", "horizontal"]:
            raise ValueError("Argument 'orientation' must be either vertical "
                             "or horizontal")
        if not expand in ["both", "row", "column"]:
            raise ValueError("Argument 'expand' must be either row, column, "
                             "or both")
        self._w_kwargs = {} if wkwargs is None else wkwargs
        self._w_orientation = {"vertical": "v", "horizontal": "h"}[orientation]
        self._w_widget = unit_widget
        self._w_expand = expand

        self._widget_list = []
        self._widget_dict = {}

        super().__init__(master, **kwargs)

        self._add_widget()
        self._create_widgets()

        self._configure_binding = {}
        self._last_configured = datetime.min
        self.bind_configure(self)

    @log_class
    def set_minmax(self, minmax = None):
        """ Set the minimum and maximum number of widgets """
        if minmax is None:
            self._w_count_min, self._w_count_max = (0, float('inf'))
        else:
            min, max = minmax
            min = 0 if min is None else min
            max = float('inf') if max is None else max
            self._w_count_min, self._w_count_max = (min, max)

    @log_class
    def _add_widget(self):
        """ Add an instance of the widget to the end of the collection """
        widget = self._w_widget(self, **self._w_kwargs)
        index = self.count()
        self._widget_list.append(widget)
        self._widget_dict[index] = widget
        self._place_widget(widget, index)

    @log_class
    def _remove_widget(self, index = None):
        """ Remove a specific widget, defaulting to the last one """
        if index is None:
            index = self.count() - 1
        widget = self._widget_dict[index]
        widget.grid_forget()
        self._widget_list.remove(widget)
        del self._widget_dict[index]

    @log_class
    def _place_widget(self, widget, index):
        if self._w_orientation == "v":
            widget.grid(row = index, column = 0, **c.GRID_STICKY)
        if self._w_orientation == "h":
            widget.grid(row = 0, column = index, **c.GRID_STICKY)

        self._handle_expand(index)

    @log_class
    def _handle_expand(self, index):
        if self._w_orientation == "v":
            idict = {"row": index, "column": 0}
        elif self._w_orientation == "h":
            idict = {"row": 0, "column": index}
        else:
            raise ValueError

        if self._w_expand in ["row", "both"]:
            self.rowconfigure(idict["row"], weight = 1)

        if self._w_expand in ["column", "both"]:
            self.columnconfigure(idict["column"], weight = 1)

    @log_class
    def get_widgets(self):
        """ Return a list of widgets, ordered by placement top to bottom / left
        to right """
        return self._widget_list

    @log_class
    def get_widgets_dict(self):
        """ Return a dictionary of widgets with keys the index of their
        placement in the collection """
        return self._widget_dict

    @log_class
    def count(self):
        """ Return the number of currently placed widgets """
        return len(self._widget_list)

    @log_class
    def get_available_height(self):
        """ Get space available for widgets to be added """
        return self.winfo_height()

    @log_class
    def _get_max_widgets(self):
        """ Get maximum number of widgets that will fit based on available
        space. """
        #TODO - horizontal placement
        widget_height = self._widget_list[0].winfo_height()
        available_height = self.get_available_height()
        if available_height == 0:
            return 0
        else:
            return available_height // widget_height

    @log_class
    def allow_configure(self, bln):
        """ Allow automatic placement/removal of widgets triggered by the
        <Configure> event """
        self._allow_configure = bln

    @log_class
    def bind_configure(self, widget = None):
        """ Bind the automatic placement/removal of widgets to the <Configure>
        event of a specific function. If no widget is given, rebind all widgets
        previously bound. """
        if widget is None:
            for wdgt in self._configure_binding:
                self._bind_configure(wdgt)
        else:
            self._bind_configure(widget)

    @log_class
    def _bind_configure(self, widget):
        if not self._configure_binding.get(widget, None) is None:
            # don't bind again if one already exists
            return
        binding = widget.bind("<Configure>", self._configure, add = "+")
        self._configure_binding[widget] = binding

    @log_class
    def unbind_configure(self, widget = None):
        """ Unbind the automatic placement/removal of widgets from the
        <Configure> event of a specific function. If no widget is given,
        unbind all widgets currently bound. """
        if widget is None:
            for wdgt in self._configure_binding:
                self._unbind_configure(wdgt)
        else:
            self._unbind_configure(widget)

    @log_class
    def _unbind_configure(self, widget):
        binding = self._configure_binding[widget]
        if binding is None:
            return
        widget.unbind("<Configure>", binding)
        self._configure_binding[widget] = None

    @log_class
    def _configure(self, *args, **kwargs):
        """ Called when <Configure> event is triggered. """
        if not self._allow_configure:
            return
        if (datetime.now() - self._last_configured).total_seconds() < 0.1:
            return
        # Temporarily unbind and then rebind the configure callback to prevent
        # infinite loops from creating widgets inside this function
        self.unbind_configure()
        self._last_configured = datetime.now()
        if self._create_widgets():
            self.event_generate("<<CountChange>>")
        self.bind_configure()

    @log_class
    def _create_widgets(self):
        """ Add or remove widgets based on the current number, available space,
        and restrictions. Generate virtual event and return True if the number
        of widgets has changed """
        max_widgets = min(max(self._get_max_widgets(),
                              self._w_count_min),
                          self._w_count_max)
        num_widgets = self.count()
        create = False
        # add new title modules until max number is reached
        if num_widgets < max_widgets:
            for i in range(max_widgets - num_widgets):
                self._add_widget()
            create = True
        elif num_widgets == max_widgets:
            create = False
        # or remove until max number is reached
        else:
            removals = [i for i in self._widget_dict if i+1 > max_widgets]
            for i in removals:
                self._remove_widget(i)
            create = len(removals) > 0

        if create:
            self.event_generate("<<CountChange>>")
        return create

polygon_db = MultiConnection(
    r".\data\polygon.db",
    ["series", "episodes", "titles", "entries", "entry_tags", "title_tags",
     "watchlist"],
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
            btn_start_rec.grid(row = 1, column = 0, **c.GRID_STICKY)

            self.root.mainloop()

        @log_class
        def start_window(self):
            title_bar = PolygonWindowBase(self.root, title = "TEST WINDOW")
            btn_stop_rec = tk.Button(
                title_bar.window, text = "btn2",
                font = ("Constantia", 32, "bold"))
            btn_stop_rec.grid(row = 1, column = 0, **c.GRID_STICKY)
            title_bar.start()

    app = TestApp()
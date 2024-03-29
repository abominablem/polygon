# -*- coding: utf-8 -*-
"""
Created on Thu Jan  6 20:24:28 2022

@author: marcu
"""
import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import tkinter.filedialog
import tkinter as tk
from PIL import Image, ImageTk

from mh_logging import log_class
import tk_arrange as tka
from PIL_util import pad_image_with_transparency
from sqlite_tablecon import MultiConnection
import constants as c
import prospero.constants as pr_c

from datetime import datetime

log_class = log_class(c.LOG_LEVEL)

class PolygonException(Exception):
    pass

class PolygonFrameBase:
    """ Base tk.Frame with menu, Polygon logo, and title bar """
    @log_class
    def __init__(self, master, title = "Polygon", logo = None, **kwargs):
        self.master = master
        self.widget_frame = tk.Frame(self.master, bg = c.COLOUR_BACKGROUND)
        """ Draw logo"""
        logo = c.LOGO_PATH if logo is None else logo
        with Image.open(logo) as image:
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

        if name in self.icons:
            raise ValueError("Name already used within icon set")

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
            icon.bind("<Enter>", self._bound_enter_func)
            icon.bind("<Leave>", self._bound_leave_func)

        # update the foreground colour when the icon is the last one clicked
        if not select is None:
            self._icon_colours[name]['select'] = select
            icon.bind("<1>", self._bound_click_func)

        self.icons[name] = icon
        return icon

    @log_class
    def _bound_enter_func(self, event):
        """ Bound to the <Enter> event of each icon """
        w = event.widget
        self._icon_colours[w.name]["current"] = w.cget('fg')
        w.config(fg = self._icon_colours[w.name]["hover"])

    @log_class
    def _bound_leave_func(self, event):
        """ Bound to the <Leave> event of each icon """
        w = event.widget
        w.config(fg = self._icon_colours[w.name]["current"])

    @log_class
    def _bound_click_func(self, event):
        """ Bound to the <1> event of each icon """
        w = event.widget
        for iname in self.icons:
            if iname != w.name:
                self[iname].config(fg = self._icon_colours[iname]['fg'])
        col = self._icon_colours[w.name]["select"]
        self._icon_colours[w.name]["current"] = col
        w.config(fg = col)

    @log_class
    def select(self, name):
        """ Simulate selecting an icon """
        event = IconDummyEvent(widget = self.icons[name])
        self._bound_click_func(event)

    def __getitem__(self, name):
        return self.icons[name]

class IconDummyEvent:
    """ Dummy class used to hold some specific attributes, simulating a tk
    event """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

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
        self._allow_configure = True
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

    def __getitem__(self, index):
        return self.get_widgets()[index]

class FolderSelection(tk.Frame):
    def __init__(self, master, text = None, name = None, **kwargs):
        super().__init__(master, **kwargs)
        self.selectors = {
            0: FolderSelector(self, text = text, name = name, row = 0)
            }
        self.columnconfigure(1, weight = 1)

    def config_entry(self, **kwargs):
        for selector in self.selectors.values():
            selector.config_entry(**kwargs)

    def config_button(self, **kwargs):
        for selector in self.selectors.values():
            selector.config_button(**kwargs)

    def config_text(self, **kwargs):
        for selector in self.selectors.values():
            selector.config_text(**kwargs)

    def add(self, text = None, name = None):
        row = max(self.selectors) + 1
        self.selectors[row] = FolderSelector(
            self, text = text, name = name, row = row)

    def get_value(self):
        return {selector.name: selector.get_value()
                for selector in self.selectors}

    def __getitem__(self, name):
        try:
            return self.selectors[name]
        except KeyError:
            for fs in self.selectors.values():
                if fs.name == name: return fs
        raise ValueError("No selector %s" % name)

class FolderSelector:
    def __init__(self, master, text = None, name = None, row = 0):
        " If specified, create a text label in the first column "
        self.master = master
        self._text = text
        self.name = row if name is None else name
        if not text is None:
            self.text = tk.Label(master, text = text)

        sv = tk.StringVar()
        sv.trace_add("write", self._entry_write)
        self.entry = tk.Entry(master, textvariable = sv)
        self.button = tk.Button(
            master, text = "Update directory", command = self._button_click)

        self.text.grid(row = row, column = 0, **c.GRID_STICKY_PADDING_SMALL)
        self.entry.grid(row = row, column = 1, **c.GRID_STICKY_PADDING_SMALL)
        self.button.grid(row = row, column = 2, **c.GRID_STICKY_PADDING_SMALL)

    def get_value(self):
        value = self.value
        if not value[-1] == "/":
            value += "/"
        return value

    def set_value(self, value):
        self.value = value
        self.entry.delete(0, "end")
        self.entry.insert(0, self.value)
        self.master.event_generate("<<ValueChange>>")

    def _entry_write(self, *args, **kwargs):
        self.set_value(self.entry.cget('sv').get())

    def _button_click(self, *args, **kwargs):
        value = tk.filedialog.askdirectory(title = 'Select a directory')
        self.set_value(value)

    def config_entry(self, **kwargs):
        self.entry.config(**kwargs)

    def config_button(self, **kwargs):
        self.button.config(**kwargs)

    def config_text(self, **kwargs):
        self.text.config(**kwargs)

class ProsperoIOSelector(FolderSelection):
    def __init__(self, master, **kwargs):
        super().__init__(
            master, text = "Input directory", name = "input", **kwargs)
        self.add(text = "Output directory", name = "output")
        self.config_text(**pr_c.PR_LABEL_STANDARD_ARGS)
        self.config_entry(**pr_c.PR_ENTRY_LARGE_ARGS)
        for selector in self.selectors.values():
            selector.config_button(
                **pr_c.PR_BUTTON_LIGHT_STANDARD_ARGS,
                text = "Change %s directory" % selector.name
                )

polygon_db = MultiConnection(
    r".\data\polygon.db",
    ["series", "episodes", "titles", "entries", "entry_tags", "title_tags",
     "watchlist"],
    debug = c.DEBUG
    )

prospero_db = MultiConnection(
    r".\prospero\data\prospero.db",
    ["config", "renames", "regex_patterns"],
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

    class TestAppFolderSelection:
        @log_class
        def __init__(self):
            self.root = tk.Tk()
            btn_start_rec = FolderSelection(self.root, text = "Input directory", name = "input", bg = "orange")
            btn_start_rec.add_selector("Output directory", name = "output")
            self.root.columnconfigure(0, weight = 1)
            btn_start_rec.grid(row = 1, column = 0, **c.GRID_STICKY)
            self.root.mainloop()

    app = TestAppFolderSelection()
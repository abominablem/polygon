# -*- coding: utf-8 -*-
"""
Created on Wed Apr  7 23:22:23 2021

@author: marcu
"""
# package imports
import tkinter as tk
from tkinter import ttk
import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")

# custom packages
import tk_arrange as tka
from mh_logging import log_class

# polygon imports
import base

# custom imports
import prospero.constants as c
import prospero.naming as naming
# from value_insight import Insight

log_class = log_class(c.LOG_LEVEL)

class Prospero(tk.Toplevel):
    @log_class
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Prospero - MP3 file handling and ID3v2 tagging")
        self.iconphoto(True, tk.PhotoImage(file = c.PR_LOGO_SMALL_PATH))
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.columnconfigure(0, weight = 1)
        self.rowconfigure(0, weight = 1)
        self._style(self)

        icon_kwargs = dict(
            bg = c.PR_COLOUR_PROSPERO_BLUE,
            padx = 20, anchor = "center", fg = c.COLOUR_TITLEBAR_ICON,
            cursor = "hand2", hover = c.COLOUR_TITLEBAR_ICON_HOVER,
            select = c.COLOUR_TITLEBAR_ICON_SELECTED
            )

        """ Header with logo and title """
        self.widget_frame = tk.Frame(self, bg = c.PR_COLOUR_BACKGROUND)
        self.header = base.PolygonFrameBase(
            self.widget_frame, logo = c.PR_LOGO_PATH, title = "Prospero",
            )
        self.header.title.config(
            bg = c.PR_COLOUR_PROSPERO_BLUE, font = c.PR_FONT_TITLE)
        self.header.logo.config(bg = c.PR_COLOUR_PROSPERO_BLUE)

        """ Icons """
        self.icons = base.IconSet(
            self.widget_frame, bg = c.PR_COLOUR_PROSPERO_BLUE)
        self.icons.rowconfigure(0, weight = 1)

        self.icons.add(text = "✍", name = "naming", **icon_kwargs, font = ("Calibri", 55, "bold"))
        self.icons.add(text = "🎧", name = "audio", **icon_kwargs, font = ("Calibri", 40))
        for name in ["naming", "audio"]:
            self.icons[name].bind(
                "<1>", lambda event: self.launch_module(event.widget.name),
                add = "+"
                )

        self.divider = tk.Frame(self.widget_frame, bg = "black", height = 1)

        self.view_naming = naming.Naming(
            self.widget_frame, bg = c.PR_COLOUR_BACKGROUND)

        widgets = {1: {'widget': self.header, 'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True},
                   2: {'widget': self.divider, 'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True, 'stretch_height': False},
                    3: {'widget': self.view_naming, 'grid_kwargs': c.GRID_STICKY,
                        'stretch_width': True, 'stretch_height': True},
                   4: {'widget': self.icons,
                       'grid_kwargs': {**c.GRID_STICKY, "padx": (0, 0)}},
                   }
        self.widget_set = tka.WidgetSet(
            self.widget_frame, widgets, layout = [[1, 4], [2], [3]])

        self.widget_set.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.icons.select("naming")

    @log_class
    def destroy(self, event = None):
        self.running = False
        self.quit()
        super().destroy()
        base.polygon_db.close()

    @log_class
    def start(self):
        # self.eval('tk::PlaceWindow . center')
        self.mainloop()

    @log_class
    def launch_module(self, module):
        widgets = {"namning": self.view_naming, "audio": None}

        for name, wdgt in widgets.items():
            if name != module:
                wdgt.grid_forget()
            else:
                wdgt.grid(**self.widget_set._get_grid_refs(3), **c.GRID_STICKY)

    @log_class
    def _style(self, master):
        self.style = ttk.Style(master)
        self.style.theme_use("clam")
        #This handles the styling for the Treeview HEADER
        self.style.configure("TTreeview.Header",
                              background = c.PR_COLOUR_BOX_HEADER,
                              rowheight = c.PR_TREEVIEW_HEADER_HEIGHT,
                              font = c.PR_FONT_BOX_HEADER)
        #This handles the styling for the Treeview BODY
        self.style.configure("TTreeview",
                              background = c.PR_COLOUR_BOX_INTERIOR,
                              fieldbackground = c.PR_COLOUR_BOX_INTERIOR,
                              rowheight = c.PR_TREEVIEW_ITEM_HEIGHT,
                              font = c.PR_FONT_TEXT)
        #This handles the styling for Frames
        self.style.configure("TFrame", background = c.COLOUR_BACKGROUND)
        #This handles the styling for Labels
        self.style.configure("TLabel", background = c.COLOUR_BACKGROUND)
        #This handles the styling for the Notebook tabs
        self.style.configure("TNotebook.Tab",
                              background = c.PR_COLOUR_INTEREST_POINT_LIGHT,
                              font = c.PR_FONT_TEXT)
        #This handles the styling for the Notebook background
        self.style.configure("TNotebook",
                              background = c.COLOUR_BACKGROUND,
                              font = c.PR_FONT_TEXT)
        #Change the coloure of the selected item
        self.style.map("TTreeview", background = [('selected', c.PR_COLOUR_SELECTION_BACKGROUND)])
        self.style.map("TNotebook.Tab", background = [('selected', c.PR_COLOUR_PROSPERO_BLUE_PASTEL)])
        self.style.map("TNotebook.Tab", foreground = [('selected', c.COLOUR_OFFWHITE_TEXT)])


"""
        # self.insight_rn = Insight(type = "renames", debug = self.testing_mode)

        self.insight_rn.define_field_map({
            "Original name": "original_name",
            "#0": "original_name",
            "Composer": "composer",
            "Album": "album",
            "#": "number",
            "Track": "track",
            "Performer(s)": "performers",
            "Year": "year",
            "Genre": "genre",
            "URL": "url",
            "Final name": "final_name"}
            )

"""


# prospero = Prospero()
# prospero.start()
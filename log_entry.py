# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 21:31:46 2022

@author: marcu
"""
import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import tkinter as tk
from widgets import TitleModule
from PIL import Image, ImageTk

from mh_logging import log_class
import tk_arrange as tka
import constants as c
import base
from imdb_functions import imdbf
import futil

log_class = log_class(c.LOG_LEVEL)

class TitleModuleEditable(TitleModule):
    @log_class
    def __init__(self, master, include_tags = True, **kwargs):
        self.master = master
        super().__init__(self.master, include_rewatch = False,
                         include_number = False, **kwargs)

        self.locked_rating = self.rating.rating
        self.rating.config(cursor = "hand2")
        self.rating.bind("<Enter>", self._enter_rating)
        self.rating.bind("<Leave>", self._leave_rating)
        self.rating.bind("<1>", self.lock_rating)

        with Image.open(r".\common\tag_outlined_thin.png") as image:
            self.add_tag_icon = ImageTk.PhotoImage(image.resize((100, 100)))
        self.add_tag = tk.Label(self.master, image = self.add_tag_icon,
                                cursor = "hand2")
        self.add_tag.grid(row = 0, column = 1, **c.GRID_STICKY, padx = 20)

    @log_class
    def _enter_rating(self, event):
        """ Triggered by cursor entering rating widget """
        self._bind_hover_rating()

    @log_class
    def _leave_rating(self, event):
        """ Triggered by cursor leaving rating widget """
        self._unbind_hover_rating()
        self.rating.set(self.locked_rating)

    @log_class
    def _bind_hover_rating(self):
        """ Bind the mouse move event to update rating_display """
        self._hover_rating_binding  = self.rating.bind(
            "<Motion>", self.rating.set_mouseover_rating)

    @log_class
    def _unbind_hover_rating(self):
        """ Unbind the mouse move event from rating_display"""
        self.rating.unbind(self._hover_rating_binding)

    @log_class
    def lock_rating(self, event):
        """ Lock the current rating in as the displayed rating """
        self.locked_rating = self.rating.rating

# class LogEntryWindow(tk.Toplevel):
class LogEntryWindow(tk.Frame):
    """ Window to log film entry """
    @log_class
    def __init__(self, master, *args, **kwargs):
        self.master = master
        super().__init__(master, *args, **kwargs)
        self.data = TitleModuleEditable(self.master)
        self.data.grid(row = 0, column = 0, **c.GRID_STICKY)

if __name__  == "__main__":
    root = tk.Tk()
    log = LogEntryWindow(root)
    log.data.set_text(
            date = "2022-01-22", title = "The Last Duel",
            director = "Ridley Scott", original_title = "The Last Duel",
            year = 2021, runtime = "156", rating = 6
            )
    log.grid(row = 0, column = 0, **c.GRID_STICKY)

    root.overrideredirect(True)
    root.lift()
    root.wm_attributes("-topmost", True)
    root.wm_attributes("-transparentcolor", "#F0F0F0")
    root.bind("<Escape>", lambda event: root.destroy())
    root.eval('tk::PlaceWindow . center')
    root.mainloop()
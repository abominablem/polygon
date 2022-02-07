# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 21:31:46 2022

@author: marcu
"""
import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import tkinter as tk
from tkinter import ttk, simpledialog
from widgets import TitleModule
from PIL import Image, ImageTk

from mh_logging import log_class
import tk_arrange as tka
import constants as c
import base
from imdb_functions import imdbf
import futil
import log_entry_tag as tagf

log_class = log_class(c.LOG_LEVEL)

class TagSelection(tk.Toplevel):
    tag_name_new = " - New - "
    @log_class
    def __init__(self, master, *args, **kwargs):
        self.master = master
        super().__init__(master, *args, **kwargs)

        self.widget_frame = tk.Frame(self, bg = c.COLOUR_FILM_BACKGROUND)

        self.text = tk.Label(
            self.widget_frame, fg = c.COLOUR_OFFWHITE_TEXT,
            font = ("Helvetica", 24), bg = c.COLOUR_FILM_BACKGROUND,
            text = "Add tags to this entry:"
            )

        self.tag_name = tk.StringVar(self.widget_frame)
        self.tag_value = tk.StringVar(self.widget_frame)

        self.current_tags = self.get_tag_combinations()
        self.current_tag_names = self.get_tag_names()
        self.tag_name_dropdown = ttk.OptionMenu(
            self.widget_frame, self.tag_name,
            "None", self.tag_name_new, *self.current_tag_names,
            command = self.tag_name_change
            )

        self.tag_value_entry = tk.Entry(
            self.widget_frame, textvariable = self.tag_value,
            font = ("Helvetica", 24)
            )

        widgets = {1: {'widget': self.text,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True},
                   2: {'widget': self.tag_name_dropdown,
                       'grid_kwargs': {**c.GRID_STICKY, "padx": 2, "pady": 10},
                       'stretch_width': True,},
                   3: {'widget': self.tag_value_entry,
                       'grid_kwargs': {**c.GRID_STICKY, "padx": 2, "pady": 10},
                       'stretch_width': True,},
                   }

        self.widget_set = tka.WidgetSet(
            self.widget_frame, widgets = widgets, layout = [[1], [2, 3]]
            )
        self.widget_set.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

    @log_class
    def start(self):
        self.master.eval('tk::PlaceWindow %s center' % str(self))
        self.lift()
        self.transient(self.master)
        self.grab_set()
        self.mainloop()

    @log_class
    def tag_name_change(self, *args):
        if self.tag_name.get() == self.tag_name_new:
            self.ask_new_tag_name()

    @log_class
    def get_tag_combinations(self):
        query = "SELECT DISTINCT tag_name, tag_value FROM entry_tags"
        result = base.polygon_db.entries.select(query)
        return result

    @log_class
    def get_tag_names(self):
        """ Get list of distinct tag names already used """
        names = list({tag[0] for tag in self.current_tags})
        return names

    @log_class
    def get_tag_values(self, name):
        """ Get list of distinct tag values already used in association with
        a certain tag name """
        names = list({tag[1] for tag in self.current_tags if tag[0] == name})
        return names

    @log_class
    def get_tag(self):
        name, value = self.tag_name.get(), self.tag_value.get()
        if name.strip().lower() == "none": name = None
        return {name: value}

    @log_class
    def get_dict(self):
        tag = self.get_tag()
        return {"name": list(tag)[0], "value": list(tag.values())[0]}

    @log_class
    def ask_new_tag_name(self):
        name = simpledialog.askstring(
            "Input", "Enter a new tag name", parent = self
            )
        self.tag_name.set(name)


class TitleModuleEditable(TitleModule):
    @log_class
    def __init__(self, master, include_tags = True, **kwargs):
        self.master = master
        super().__init__(self.master, include_rewatch = False,
                         include_number = False, **kwargs,
                         bg = c.COLOUR_TRANSPARENT)

        self.rating.set_range(min = 0)
        self.rating.set(0)
        self.locked_rating = self.rating.rating
        self.rating.config(cursor = "hand2")
        self.rating.bind("<Enter>", self._enter_rating)
        self.rating.bind("<Leave>", self._leave_rating)
        self.rating.bind("<1>", self.lock_rating)

        with Image.open(r".\common\tag_outlined_thin.png") as image:
            self.tag_icon_image = ImageTk.PhotoImage(image.resize((100, 100)))
        self.tag_icon = tk.Label(self.master, image = self.tag_icon_image,
                                cursor = "hand2", bg = c.COLOUR_TRANSPARENT)
        self.tag_icon.bind("<1>", self._click_tag_icon)
        self.tag_icon.grid(row = 0, column = 1, **c.GRID_STICKY, padx = 20)

        self.tag_frame = tk.Frame(self.master, bg = c.COLOUR_TRANSPARENT)
        self.tag_frame.grid(row = 1, column = 0, columnspan = c.COLUMNSPAN_ALL,
                            **c.GRID_STICKY, padx = 10, pady = 10)
        self._tag_images = {}
        self._tag_widgets = {}
        self.tags = {}
        self._tag_count = 0

    @log_class
    def _enter_rating(self, event):
        """ Triggered by cursor entering rating widget """
        self._bind_hover_rating()

    @log_class
    def _leave_rating(self, event):
        """ Triggered by cursor leaving rating widget """
        self._unbind_hover_rating()
        # reset the rating slightly after leaving the widget
        self.after(100, lambda: self.rating.set(self.locked_rating))

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

    @log_class
    def _click_tag_icon(self, event):
        """ Called when the tag icon image is left clicked """
        self.ask_tag()

    @log_class
    def ask_tag(self, *args):
        """ Open an interface to select the tag name and value """
        self.tag_window = TagSelection(root)
        self.tag_window.lift()
        self.tag_window.bind("<Return>", self.get_tag)
        self.tag_window.start()

    def get_tag(self, *args):
        """ Get the tag details from the open tag window, and then close it """
        self.add_tag(**self.tag_window.get_dict())
        self.tag_window.destroy()

    @log_class
    def add_tag(self, name, value):
        """ Add a tag to the tag dictionary, and add a tag image below the
        window """
        self.add_tag_dict(name, value)
        self.add_tag_image(name, value)

    @log_class
    def add_tag_dict(self, name, value):
        """ Add a tag to the tag dictionary """
        if name in self.tags:
            self.tags[name].append(value)
        else:
            self.tags[name] = [value]

    @log_class
    def add_tag_image(self, name, value):
        """ Add a tag image below the window """
        if name is None:
            tag_string = value
        else:
            tag_string = f"{name}: {value}"

        tag_col = self.get_tag_count()

        # the standard image to show
        tag_img = ImageTk.PhotoImage(
            image = tagf.text_tag(tag_string, height = 60)
            )
        # the image to show when hovered over (darker cross)
        tag_img_hover = ImageTk.PhotoImage(
            image = tagf.text_tag(tag_string, height = 60, x_colour = "gray")
            )
        self._tag_images[tag_col] = {"standard": tag_img,
                                     "hover": tag_img_hover}
        # create labels
        tag_widget = tk.Label(
            self.tag_frame, image = tag_img, cursor = "hand2",
            bg = c.COLOUR_TRANSPARENT
            )
        self._tag_widgets[tag_col] = tag_widget

        tag_widget.grid(row = 0, column = tag_col)
        tag_widget.bind(
            "<Enter>", lambda *args: self._enter_tag_widget(tag_col)
            )
        tag_widget.bind(
            "<Leave>", lambda *args: self._leave_tag_widget(tag_col)
            )
        tag_widget.bind(
            "<ButtonRelease-1>", lambda *args: self._click_tag_widget(tag_col)
            )
        # iterate the counter so next tag is added to next column along
        self._tag_count += 1

    def _enter_tag_widget(self, column):
        """ Set hover image on entering tag widget """
        self._tag_widgets[column].config(
            image = self._tag_images[column]["hover"]
            )

    def _leave_tag_widget(self, column):
        """ Set standard image on entering tag widget """
        self._tag_widgets[column].config(
            image = self._tag_images[column]["standard"]
            )

    def _click_tag_widget(self, column):
        """ Remove widget on clicking tag """
        self.after(100, lambda: self._tag_widgets[column].grid_forget())


    def get_tag_count(self):
        return self._tag_count


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
    root.configure(bg = c.COLOUR_TRANSPARENT)
    log = LogEntryWindow(root, bg = c.COLOUR_TRANSPARENT)
    log.data.set_text(
            date = "2022-01-22", title = "The Last Duel",
            director = "Ridley Scott", original_title = "The Last Duel",
            year = 2021, runtime = "156"
            )
    log.grid(row = 0, column = 0, **c.GRID_STICKY)

    root.overrideredirect(True)
    root.lift()
    root.wm_attributes("-transparentcolor", c.COLOUR_TRANSPARENT)
    root.bind("<Escape>", lambda event: root.destroy())
    root.eval('tk::PlaceWindow . center')
    style = ttk.Style(root)
    style.theme_use("clam")

    def log(event = None):
        loge = TagSelection(root)
        loge.mainloop()

    root.bind("<Return>", log)

    root.mainloop()
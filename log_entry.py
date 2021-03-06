# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 21:31:46 2022

@author: marcu
"""
import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import tkinter as tk
from tkinter import ttk, simpledialog
from widgets import (TitleModule, HoverIconTick, HoverIconCross, HoverIconPath,
                     HoverIconTag)
import tkcalendar as tkcal
from datetime import datetime

from mh_logging import log_class
import tk_arrange as tka
import constants as c
import base
from futil import get_tk

log_class = log_class(c.LOG_LEVEL)

class TagSelection(tk.Toplevel):
    tag_name_new = " - New - "
    @log_class
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.widget_frame = base.TrimmedFrame(self)
        self.widget_frame.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.widget_frame.rowconfigure(0, weight = 1)
        self.widget_frame.columnconfigure(0, weight = 1)

        self.icon_frame = tk.Frame(self, bg = c.COLOUR_TRANSPARENT)
        self.icon_frame.grid(row = 0, column = 1, **c.GRID_STICKY)

        self.x_label = HoverIconCross(
            self.icon_frame, bg = c.COLOUR_TRANSPARENT, height = 50,
            anchor = "n"
            )
        self.x_label.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.x_label.bind("<1>", self._click_x)

        label_padding = tk.Frame(self.icon_frame, bg = c.COLOUR_TRANSPARENT)
        label_padding.grid(row = 1, column = 0, **c.GRID_STICKY)
        self.icon_frame.rowconfigure(1, weight = 1)

        self.tick_label = HoverIconTick(
            self.icon_frame, bg = c.COLOUR_TRANSPARENT, height = 50,
            anchor = "s"
            )
        self.tick_label.grid(row = 2, column = 0, **c.GRID_STICKY)
        self.tick_label.bind("<1>", self._click_tick)

        self.text = tk.Label(
            self.widget_frame.inner, font = ("Helvetica", 24),
            text = "   Add tags to this entry:", anchor = "w"
            )

        self.tag_name = tk.StringVar(self.widget_frame.inner)
        self.tag_value = tk.StringVar(self.widget_frame.inner)

        self.current_tags = self.get_tag_combinations()
        self.current_tag_names = self.get_tag_names()
        self.tag_name_dropdown = ttk.OptionMenu(
            self.widget_frame.inner, self.tag_name,
            "None", self.tag_name_new, *self.current_tag_names,
            command = self.tag_name_change, style = 'entrytag.TMenubutton'
            )

        self.tag_value_entry = tk.Entry(
            self.widget_frame.inner, textvariable = self.tag_value,
            font = ("Helvetica", 24)
            )

        self._suggested_tags = []

        widgets = {1: {'widget': self.text,
                       'grid_kwargs': c.GRID_STICKY,
                       'stretch_width': True},
                   2: {'widget': self.tag_name_dropdown,
                       'grid_kwargs': {**c.GRID_STICKY, "padx": (10, 2), "pady": 10},
                       'stretch_width': True,},
                   3: {'widget': self.tag_value_entry,
                       'grid_kwargs': {**c.GRID_STICKY, "padx": (2, 10), "pady": 10},
                       'stretch_width': True,},
                   }

        self.widget_set = tka.WidgetSet(
            self.widget_frame.inner, widgets = widgets, layout = [[1], [2, 3]]
            )
        self.widget_set.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

        self.wm_attributes("-transparentcolor", c.COLOUR_TRANSPARENT)

    @log_class
    def start(self, position = None):
        # set the startup position as a pixel tuple (x, y)
        if not position is None:
            geometry = "+%s+%s" % position
            self.geometry(geometry)

        self.overrideredirect(True)
        self.lift()
        self.grab_set()
        self.tag_value_entry.focus()
        self.mainloop()

    @log_class
    def tag_name_change(self, *args):
        """ Called when the dropdown value for tag name changes """
        if self.tag_name.get() == self.tag_name_new:
            self.ask_new_tag_name()

        # generate suggested tags for new tag name
        self.clear_suggested_tags()
        self.add_tag_suggestions(self.tag_name.get())

        self.tag_value_entry.focus()

    @log_class
    def get_tag_combinations(self):
        query = "SELECT DISTINCT tag_name, tag_value FROM entry_tags"
        result = base.polygon_db.entry_tags.select(query)
        return result

    @log_class
    def get_tag_count(self):
        return len(self._suggested_tags)

    @log_class
    def get_latest_tag_values(self, name, n = 5):
        """ Get the set of n most recently used values for a tag name """
        query = """SELECT DISTINCT tag_value FROM
            entry_tags t LEFT JOIN entries e
            ON t.[entry_id] = e.entry_id
            WHERE tag_name = '%s'
            GROUP BY tag_value
            ORDER BY MAX(entry_date) DESC
            LIMIT %s""" % (name, n)
        result = base.polygon_db.entry_tags.select(query)
        return [row[0] for row in result]

    @log_class
    def clear_suggested_tags(self):
        """ Remove suggested tag images """
        for widget in self._suggested_tags:
            # fix error with leave event being triggered on grid_forget
            widget.unbind("<Leave>")
            widget.grid_forget()
        self._suggested_tags = []

    @log_class
    def add_tag_suggestions(self, name):
        """ Add tag suggestion images below the window for a given tag name """
        values = self.get_latest_tag_values(name)

        for value in values:
            tag_col = self.get_tag_count()
            tag = self.get_tag_widget(value)
            tag.grid(row = tag_col + 4, column = 0, ipady = 2, sticky = "nsw")

    @log_class
    def get_tag_widget(self, value):
        """ Get Label widget containing a tag with given text """
        tag_widget = HoverIconTag(
            self, bg = c.COLOUR_TRANSPARENT, value = value, height = 40)
        self._suggested_tags.append(tag_widget)
        tag_widget.tag_value = value

        tag_widget.bind("<ButtonRelease-1>", self._click_tag_widget)
        return tag_widget

    @log_class
    def _click_tag_widget(self, event):
        """ Set the tag value to the clicked value. Remove all suggestions """
        self.tag_value_entry.delete(0, 'end')
        self.tag_value_entry.insert(0, event.widget.tag_value)
        self.clear_suggested_tags()
        self.event_generate("<<TickClick>>")

    @log_class
    def get_tag_names(self):
        """ Get list of distinct tag names already used """
        names = list({tag[0] for tag in self.current_tags})

        return sorted(names)

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
        self.tag_value_entry.focus_force()

    @log_class
    def _click_x(self, *args):
        self.master.focus_force()
        self.destroy()

    @log_class
    def _click_tick(self, *args):
        self.event_generate("<<TickClick>>")

class EntryDateSelection(tk.Toplevel):
    @log_class
    def __init__(self, master, *args, **kwargs):
        self.master = master
        super().__init__(master, *args, **kwargs)

        now = datetime.now()
        self.calendar = tkcal.Calendar(
            self, selectmode = "day", bg = c.COLOUR_FILM_BACKGROUND,
            year = now.year, month = now.month, day = now.day
            )
        self.calendar.grid(row = 0, column = 0, **c.GRID_STICKY)

    @log_class
    def start(self, position = None):
        # set the startup position as a pixel tuple (x, y)
        if not position is None:
            geometry = "+%s+%s" % position
            self.geometry(geometry)

        self.overrideredirect(True)
        self.lift()
        self.grab_set()
        self.mainloop()

    @log_class
    def get_date(self):
        return self.calendar.get_date()


class TitleModuleEditable(TitleModule):
    @log_class
    def __init__(self, master, include_tags = True, **kwargs):
        self.master = master
        super().__init__(self.master, include_rewatch = False,
                         include_number = False, **kwargs,
                         bg = c.COLOUR_TRANSPARENT)

        self.rating.set_range(min = 0)
        self.set_text(rating = 0)
        self.locked_rating = self.rating.rating
        self.rating.config(cursor = "hand2")
        self.rating.bind("<Enter>", self._enter_rating)
        self.rating.bind("<Leave>", self._leave_rating)
        self.rating.bind("<1>", self.lock_rating)

        self.base_module.date.config(cursor = "hand2")
        self.base_module.date.bind("<1>", self._click_date)

        self.tag_icon = HoverIconPath(
            self.master, bg = c.COLOUR_TRANSPARENT, dimensions = (100, 100),
            standard = r".\common\tag_outlined.png",
            hover = r".\common\tag_outlined_hover.png"
            )
        self.tag_icon.bind("<1>", self._click_tag_icon)
        self.tag_icon.grid(row = 0, column = 2, **c.GRID_STICKY, padx = 20)

        # frame for the tag images
        self.tag_frame = tk.Frame(self.master, bg = c.COLOUR_TRANSPARENT)
        self.tag_frame.grid(row = 1, column = 0, columnspan = c.COLUMNSPAN_ALL,
                            **c.GRID_STICKY, padx = 10, pady = 10)

        self._tag_widgets = {}
        self.tags = {}
        self.tag_dicts = {}
        self._tag_count = 0

        self.calendar_open = False

    @log_class
    def get_values(self):
        val_dict = self.get_dict()
        if val_dict["rating"] == 0: val_dict["rating"] = None
        return_dict = {
            "entry_date": val_dict["date"],
            "rating": val_dict["rating"],
            "tags": self.tags
            }
        return return_dict

    @log_class
    def _enter_rating(self, event):
        """ Triggered by cursor entering rating widget """
        self._bind_hover_rating()

    @log_class
    def _leave_rating(self, event):
        """ Triggered by cursor leaving rating widget """
        self._unbind_hover_rating()
        # reset the rating slightly after leaving the widget
        self.after(100, lambda: self.set_text(rating = self.locked_rating))

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
        self.tag_window = TagSelection(
            self.master, bg = c.COLOUR_TRANSPARENT)
        self.tag_window.lift()
        self.tag_window.bind("<Return>", self.get_tag)
        self.tag_window.bind("<<TickClick>>", self.get_tag)
        self.tag_window.start(position = self.get_tag_startup_position())

    @log_class
    def get_tag_startup_position(self):
        x = self.winfo_rootx() + int(self.winfo_width() * 5/7)
        y = self.winfo_rooty() + self.winfo_height() + 10
        return (x, y)

    @log_class
    def get_tag(self, *args):
        """ Get the tag details from the open tag window, and then close it """
        tag_dict = self.tag_window.get_dict()
        if not (tag_dict["value"] is None or tag_dict["value"] == ""):
            self.add_tag(**tag_dict)
        self.tag_window.destroy()
        self.event_generate("<<SubwindowClose>>")

    @log_class
    def add_tag(self, name, value):
        """ Add a tag to the tag dictionary, and add a tag image below the
        window """
        self.add_tag_dict(name, value)
        self.add_tag_image(name, value)
        # the tag window grabs the set away from this one, so grab it back when
        # done
        self._increment_tag_count()

    @log_class
    def add_tag_dict(self, name, value):
        """ Add a tag to the tag dictionary """
        if name in self.tags:
            self.tags[name].append(value)
        else:
            self.tags[name] = [value]
        self.tag_dicts[self.get_tag_count()] = {"name": name, "value": value}

    @log_class
    def add_tag_image(self, name, value):
        """ Add a tag image below the window """
        if name is None:
            tag_string = value
        else:
            tag_string = f"{name}: {value}"

        tag_col = self.get_tag_count()

        # create labels
        tag_widget = HoverIconTag(
            self.tag_frame, bg = c.COLOUR_TRANSPARENT, value = tag_string,
            height = 60)
        self._tag_widgets[tag_col] = tag_widget

        tag_widget.grid(row = 0, column = tag_col)
        tag_widget.bind(
            "<ButtonRelease-1>", lambda *args: self._click_tag_widget(tag_col)
            )

    @log_class
    def _increment_tag_count(self):
        """ Increase the tag count by one """
        self._tag_count += 1

    @log_class
    def _click_tag_widget(self, column):
        """ Remove widget on clicking tag """
        if self.calendar_open:
            return
        self.after(100, lambda: self._tag_widgets[column].grid_forget())
        tag_dict = self.tag_dicts[column]
        del self.tag_dicts[column]
        self.tags[tag_dict["name"]].remove(tag_dict["value"])

    @log_class
    def get_tag_count(self):
        return self._tag_count

    @log_class
    def _click_date(self, *args):
        self.launch_calendar()

    @log_class
    def get_calendar_startup_position(self):
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 10
        return (x, y)

    @log_class
    def launch_calendar(self):
        self.calendar_open = True
        self.calendar = EntryDateSelection(
            self.master, bg = c.COLOUR_FILM_BACKGROUND
            )
        self.calendar.focus_force()
        self.calendar.bind("<Double-1>", self.get_calendar_date)
        self.calendar.bind("<Escape>", self.exit_calendar)

        self.calendar.start(position = self.get_calendar_startup_position())

    @log_class
    def exit_calendar(self, *args):
        self.calendar.destroy()
        self.event_generate("<<SubwindowClose>>")
        # since the calendar will overlap the tags, don't indicate that the
        # calendar is closed until shortly after it actually is. This prevents
        # accidentally removing tags from extra clicks
        def _make_calendar_none_(*args, **kwargs):
            self.calendar_open = False
        self.after(1000, _make_calendar_none_)

    @log_class
    def get_calendar_date(self, *args):
        date = self.calendar.get_date()
        date = datetime.strptime(date, "%m/%d/%y").strftime("%Y-%m-%d")
        self.set_text(date = date)
        self.after(100, self.exit_calendar())


class LogEntryWindow(tk.Toplevel):
    """ Window to log film entry """
    @log_class
    def __init__(self, master, *args, **kwargs):
        self.master = master
        super().__init__(master, *args, **kwargs)

        self.wm_attributes("-transparentcolor", c.COLOUR_TRANSPARENT)

        self.data_frame = tk.Frame(self, bg = c.COLOUR_TRANSPARENT)
        self.data = TitleModuleEditable(self.data_frame)
        self.data.bind("<<SubwindowClose>>", self.grab_focus)
        self.data.grid(row = 0, column = 1, **c.GRID_STICKY)
        self.data_frame.grid(row = 0, column = 1, **c.GRID_STICKY)

        self.x_label = HoverIconCross(
            self, bg = c.COLOUR_TRANSPARENT, height = 100, anchor = "n")
        self.x_label.grid(row = 0, column = 0, **c.GRID_STICKY)
        self.x_label.bind("<1>", self._click_x)

        self.tick_label = HoverIconTick(
            self, bg = c.COLOUR_TRANSPARENT, height = 100, anchor = "n")
        self.tick_label.grid(row = 0, column = 2, **c.GRID_STICKY)
        self.tick_label.bind("<1>", self._click_tick)

    @log_class
    def grab_focus(self, *args, **kwargs):
        self.focus_force()
        self.lift()
        self.grab_set()

    @log_class
    def start(self):
        self.overrideredirect(True)
        # self.transient(self.master)
        self.bind("<Escape>", lambda event: self.destroy())
        self.lift()
        self.grab_set()
        get_tk(self).eval(f'tk::PlaceWindow {self} center')
        self.mainloop()

    @log_class
    def get_dict(self):
        return self.data.get_values()

    @log_class
    def _click_x(self, *args):
        self.event_generate("<<Destroy>>")
        self.destroy()

    @log_class
    def _click_tick(self, *args):
        self.event_generate("<<LogEntry>>")

    @log_class
    def set_text(self, **kwargs):
        self.data.set_text(**kwargs)


if __name__  == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.configure('entrytag.TMenubutton', font = ("Helvetica", 16))
    root.configure(bg = c.COLOUR_TRANSPARENT)
    log = LogEntryWindow(root, bg = c.COLOUR_TRANSPARENT)
    log.data.set_text(
            date = "2022-01-22", title = "The Last Duel",
            director = "Ridley Scott", original_title = "The Last Duel",
            year = 2021, runtime = "156"
            )
    log.start()
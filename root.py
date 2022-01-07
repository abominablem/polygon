# -*- coding: utf-8 -*-
"""
Created on Wed Jan  5 21:31:00 2022

@author: marcu
"""
import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
import tkinter as tk

from mh_logging import log_class
import tk_arrange as tka
import constants as c

log_class = log_class(c.LOG_LEVEL)

class Polygon:
    @log_class
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Polygon")
        self.root.protocol("WM_DELETE_WINDOW", self.destroy)

    @log_class
    def destroy(self, event = None):
        self.running = False
        self.root.quit()
        self.root.destroy()

    @log_class
    def start(self):
        self.root.eval('tk::PlaceWindow . center')
        self.root.mainloop()
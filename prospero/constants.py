# -*- coding: utf-8 -*-
"""
Created on Wed Apr 14 11:27:16 2021

@author: marcu
"""

# working directory is the top level directory, so this is ..constants
from constants import *

""" GLOBAL VARS """
PR_LOGO_PATH = ".\prospero\common\logo.png"
PR_LOGO_SMALL_PATH = ".\prospero\common\logo_small.png"

""" PADDING """
PR_WIDTH_TEXT_LONG = 400
PR_WIDTH_TEXT_MEDIUM = 300
PR_WIDTH_TEXT_SHORT = 150
PR_WIDTH_TEXT_VERYSHORT = 100
PR_WIDTH_TEXT_TINY = 50

PR_WIDTH_BUTTON_SMALL = 5
PR_WIDTH_BUTTON_LARGE = 35

PR_TREEVIEW_ITEM_HEIGHT = 20
PR_TREEVIEW_HEADER_HEIGHT = 20

PR_FILE_EXTENSION = ".MP3"

""" COLOURS """
PR_COLOUR_BACKGROUND = "#FDFCF3"
PR_COLOUR_INTERFACE_BUTTON = "#BACCBE"
PR_COLOUR_PROSPERO_BLUE = "#1C5689"
PR_COLOUR_PROSPERO_BLUE_PASTEL = "#5C86A0"
PR_COLOUR_SELECTION_BACKGROUND = "#225B8F"
PR_COLOUR_BOX_INTERIOR = COLOUR_OFFWHITE_TEXT
PR_COLOUR_BOX_HEADER = "#9AB2B0"
PR_COLOUR_INTEREST_POINT_LIGHT = "#D5E3CC"
PR_COLOUR_PROSPERO_SECONDARY_DARK = "#8D8C81"

""" FONTS """
PR_FONT_TITLE = ("Palatino Linotype", 32, "bold")
PR_FONT_LABEL_BOLD = ("Helvetica", 16, "bold")
PR_FONT_TEXT = ("Helvetica", 10)
PR_FONT_BOX_HEADER = ("Helvetica", 12, "bold")
PR_FONT_INTERFACE_BUTTON = ("Helvetica", 16, "bold")
PR_FONT_INTERFACE_BUTTON_LIGHT = ("Helvetica", 10)


""" KWARGS """
PR_LABEL_STANDARD_ARGS = {
    "background" : PR_COLOUR_BACKGROUND,
    "font" : PR_FONT_LABEL_BOLD,
    "anchor" : "w"}

PR_BUTTON_STANDARD_ARGS = {
    "background" : PR_COLOUR_INTERFACE_BUTTON,
    "font" : PR_FONT_INTERFACE_BUTTON}

PR_BUTTON_LIGHT_STANDARD_ARGS = {
    "background" : PR_COLOUR_INTERFACE_BUTTON,
    "font" : PR_FONT_INTERFACE_BUTTON_LIGHT}

PR_ENTRY_MEDIUM_ARGS = {
    "width" : 100,
    "borderwidth" : 2,
    "background" : PR_COLOUR_BOX_INTERIOR}

PR_ENTRY_LARGE_ARGS = {
    "width" : 150,
    "borderwidth" : 2,
    "background" : PR_COLOUR_BOX_INTERIOR}
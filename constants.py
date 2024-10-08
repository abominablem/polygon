# -*- coding: utf-8 -*-
"""
Created on Wed Jan  5 21:52:51 2022

@author: marcu
"""

""" COLOURS """
COLOUR_BACKGROUND = "#E8E9ED"
COLOUR_TITLEBAR = "#20063B"
COLOUR_TITLEBAR_ICON = "#F0F8FF"
COLOUR_TITLEBAR_ICON_HOVER = "#99BEFE"
COLOUR_TITLEBAR_ICON_SELECTED = "#B2CEFE"
COLOUR_OFFWHITE_TEXT = "#FEFEFE"
COLOUR_INTERFACE_BUTTON = "#D5E0D8"
COLOUR_MENU_BAR_MAIN_BACKGROUND = "White"
COLOUR_MENU_BAR_BACKGROUND = COLOUR_BACKGROUND
COLOUR_MENU_BAR_FOREGROUND = "Black"
COLOUR_MENU_BAR_ACTIVE_BACKGROUND = "#361E4E"
COLOUR_MENU_BAR_ACTIVE_FOREGROUND = COLOUR_OFFWHITE_TEXT

COLOUR_FILM_BACKGROUND = "#080808"
COLOUR_FILM_TRIM = "#00B050"
COLOUR_FILM_BUTTON_BACKGROUND = "#DEDEDE"

COLOUR_TV_BACKGROUND = COLOUR_FILM_BACKGROUND
COLOUR_TV_TRIM = COLOUR_FILM_TRIM
COLOUR_TV_BUTTON_BACKGROUND = COLOUR_FILM_BUTTON_BACKGROUND

COLOUR_TRANSPARENT = "#FF6700"

""" NUMERIC CONSTANTS """
INT_FILM_TITLES = 5
INT_FILM_TITLES_WATCHLIST = 3
INT_FILM_MIN_LENGTH = 50
MAX_REFRESH_FREQUENCY_SECONDS = 0.15

""" GLOBAL VARS """
LOG_LEVEL = "min"
DEBUG = False
LOGO_PATH = ".\common\logo.png"

""" FONTS """
FONT_MAIN_TITLE = ("Constantia", 32, "bold")
FONT_LABEL_BOLD = ("Helvetica", 16, "bold")
FONT_TEXT_DEFAULT = ("Helvetica", 10)
FONT_BOX_HEADER = ("Helvetica", 12, "bold")
FONT_INTERFACE_BUTTON = ("Helvetica", 16, "bold")
FONT_INTERFACE_BUTTON_LIGHT = ("Helvetica", 10)

""" PADDING """
PADDING_SMALL = 5
PADDING_MEDIUM = 8
PADDING_LARGE = 20

COLUMNSPAN_ALL = 100

PADDING_SMALL_TOP_ONLY = (PADDING_SMALL, 0)
PADDING_SMALL_BOTTOM_ONLY = (0, PADDING_SMALL)
PADDING_MEDIUM_TOP_ONLY = (PADDING_MEDIUM, 0)
PADDING_MEDIUM_BOTTOM_ONLY = (0, PADDING_MEDIUM)
PADDING_LARGE_TOP_ONLY = (PADDING_LARGE, 0)
PADDING_LARGE_BOTTOM_ONLY = (0, PADDING_LARGE)

PADDING_SMALL_LEFT_ONLY = (PADDING_SMALL, 0)
PADDING_SMALL_RIGHT_ONLY = (0, PADDING_SMALL)
PADDING_MEDIUM_LEFT_ONLY = (PADDING_MEDIUM, 0)
PADDING_MEDIUM_RIGHT_ONLY = (0, PADDING_MEDIUM)
PADDING_LARGE_LEFT_ONLY = (PADDING_LARGE, 0)
PADDING_LARGE_RIGHT_ONLY = (0, PADDING_LARGE)

""" DIMENSIONS """

DM_FILM_HEADER_HEIGHT = 1
DM_TV_HEADER_HEIGHT = DM_FILM_HEADER_HEIGHT

""" TK KWARGS """
GRID_STICKY = {"sticky" : "nesw"}

GRID_STICKY_PADDING_SMALL = {
    "sticky" : "nesw",
    "pady" : PADDING_SMALL,
    "padx" : PADDING_SMALL
    }

GRID_STICKY_PADDING_LARGE = {
    "sticky" : "nesw",
    "pady" : PADDING_LARGE,
    "padx" : PADDING_LARGE
    }

BTN_MAIN_ARGS = {
    "background" : COLOUR_INTERFACE_BUTTON,
    "font" : FONT_INTERFACE_BUTTON,
    "borderwidth": 3,
    "highlightthickness": 3
    }

BTN_STD_ARGS = {
    "background" : COLOUR_INTERFACE_BUTTON,
    "font" : FONT_INTERFACE_BUTTON,
    "borderwidth": 2
    }

BTN_LIGHT_ARGS = {
    "background" : COLOUR_BACKGROUND,
    "font" : FONT_INTERFACE_BUTTON_LIGHT,
    "borderwidth": 2
    }

LBL_STD_ARGS = {
    "background" : COLOUR_BACKGROUND,
    "font" : FONT_LABEL_BOLD,
    "anchor" : "w"
    }


""" IMDB CONSTANTS """
TV_TYPES = ['tv series', 'tv mini series']
MOVIE_TYPES = ['movie', 'tv movie']
EPISODE_TYPES = ['episode']
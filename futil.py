# -*- coding: utf-8 -*-
"""
Created on Wed Jan 12 21:15:11 2022

@author: marcu
"""

def list_default(list, index, default):
    try:
        return list[index]
    except IndexError:
        return default
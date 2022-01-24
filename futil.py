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


time_unit_multiplier = {
    "seconds": 1,
    "minutes": 60,
    "hours": 60 * 60,
    "days": 60 * 60 * 24,
    "years": 60 * 60 * 24 * 365
    }
time_unit_short = {
    "seconds": "s", "minutes": "m", "hours": "h", "days": "d", "years": "y"
    }
time_unit_max = {
    "seconds": 60, "minutes": 60, "hours": 24, "days": 365, "years": -1
    }
def format_time(time, unit = "seconds", round_to = "seconds"):
    unit = unit.lower()
    if unit[-1] != "s": unit += "s" # standardise to units plural
    round_to = round_to.lower()
    if round_to[-1] != "s": round_to += "s" # standardise to units plural

    if time < 0:
        raise ValueError("Time must be positive integer")
    # shortcut if
    elif time * time_unit_multiplier[unit] < time_unit_multiplier[round_to]/2:
        return "0%s" % time_unit_short[round_to]

    time *= time_unit_multiplier[unit]
    # make a multiple of the round_to multiplier
    divisor = time_unit_multiplier[round_to]
    remainder = time % time_unit_multiplier[round_to]
    if remainder/divisor >= 0.5:
        add_one = round_to
    else:
        add_one = "none"

    time = time - remainder
    time_string = ""
    # larger time units go first
    units = ["years", "days", "hours", "minutes", "seconds"]
    for i, time_unit in enumerate(units):
        duration = time // time_unit_multiplier[time_unit]
        if time_unit == add_one:
            tu_max = time_unit_max[time_unit]
            if duration + 1 >= tu_max > 0:
                add_one = units[i+1]
            else:
                duration += 1
        time = time % time_unit_multiplier[time_unit]
        if duration == 0:
            pass
        else:
            time_string += "%s%s " % (duration, time_unit_short[time_unit])

    return time_string[:-1] # trim trailing space
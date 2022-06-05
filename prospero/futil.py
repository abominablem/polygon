# -*- coding: utf-8 -*-
"""
Created on Sun Jun  5 22:46:08 2022

@author: marcu
"""

def true_titlecase(string):
    if type(string) != str:
        return([true_titlecase(entry) for entry in string])

    articles = ["a", "an", "and", "of", "the", "is", "to", "via", "for"]
    string = string.lower()
    words = string.split(" ")
    words_capitalised = (
        [words[0].capitalize()] + [
            word if word in articles else word.capitalize()
            for word in words[1:]
            ]
        )
    return " ".join(words_capitalised)
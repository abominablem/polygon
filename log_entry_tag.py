# -*- coding: utf-8 -*-
"""
Created on Sat Feb  5 23:30:08 2022

@author: marcu
"""
from PIL import Image, ImageDraw, ImageFont
import sys
sys.path.append("D:\\Users\\Marcus\\Documents\\R Documents\\Coding\\Python\\Packages")
from PIL_util import pad_image_with_transparency


def circle(draw, center, radius, fill):
    coords = (center[0] - radius + 1, center[1] - radius + 1,
              center[0] + radius - 1, center[1] + radius - 1)
    draw.ellipse(coords, fill = fill, outline = None)

def rounded_line(draw, coords, fill, width, **kwargs):
    draw.line(coords, fill = fill, width = width, **kwargs)
    circle(draw, (coords[0], coords[1]), width/2, fill)
    circle(draw, (coords[2], coords[3]), width/2, fill)

def tag(width, height, fill = "black", line_width = 15,
        background = (0, 0, 0, 0), interior = "#F3F3F3"):
    """ Return an image of a tag shaped object """
    assert width >= height * 3

    offset = line_width / 2
    if offset != int(offset):
        offset = int(offset) + 1
    else:
        offset = int(offset)
    half_height = int(height / 2)

    true_width = width + offset
    true_height = height + offset

    canvas = Image.new('RGBA', (true_width, true_height), color = background)
    draw = ImageDraw.Draw(canvas)

    """ Draw the interior shading """
    draw.rectangle(((half_height, height), (width, offset)), fill = interior)
    draw.polygon(((offset, half_height), (half_height, height),
                  (half_height, offset)), fill = interior)

    """ Draw the outside lines """
    # list of coords anti-clockwise from leftmost vertex
    coords = [(offset, half_height), (half_height, height), (width, height),
              (width, offset), (half_height, offset), (offset, half_height)]
    for i in range(len(coords)-1):
        sub_coords = coords[i] + coords[i+1]
        rounded_line(draw, sub_coords, "black", line_width)

    """ Draw the internal circle """
    radius = int((height / 3) / 2)
    circle_centre = (half_height + radius/2, half_height)
    circle(draw, circle_centre, radius, fill)

    return canvas


def _text_tag(text, text_colour = "black", x_colour = "black", fill = "black",
             line_width = 15, background = (0, 0, 0, 0), interior = "#F3F3F3"):
    """ Return an image of a tag shaped object containing a given text string
    and X """
    font = ImageFont.truetype("arial.ttf", size = 150)
    text_width, text_height = font.getsize(text)
    height = int(text_height * 1.6)
    circle_edge_x = int(height * 13/12)
    text_padding_x = int(height * 1/6)
    text_x = height
    text_y = int(height/2 - text_height/2)

    remove_tag_text = "×"
    font_remove = ImageFont.truetype("arial.ttf", size = 250)
    text_remove_width, text_remove_height = font_remove.getsize(remove_tag_text)
    text_remove_x = circle_edge_x + text_padding_x + text_width
    text_remove_y = int(height/2 - text_remove_height/2*1.2)


    width = (height + text_width + text_padding_x + text_remove_width
             + text_padding_x)

    image = tag(width, height, fill, line_width, background, interior)
    draw = ImageDraw.Draw(image)
    draw.text((text_x, text_y), text, font = font, fill = text_colour)
    draw.text((text_remove_x, text_remove_y), remove_tag_text,
              font = font_remove, fill = x_colour)
    return image

def text_tag(text, width = 1000, **kwargs):
    image = _text_tag(text, **kwargs)
    img_width, img_height = image.size
    aspect = img_width / img_height
    height = int(width / aspect)
    image = image.resize((width, height), resample=Image.ANTIALIAS)
    return image

if __name__ == "__main__":
    tag = text_tag("cost: £7.45", interior = "#808080",
                   text_colour = "white", x_colour = "#D3D3D3",
                   width = 250)
    tag.show()
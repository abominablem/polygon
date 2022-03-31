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
    # assert width >= height * 3

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

def text_tag(text, height = 300, dimensions = False, **kwargs):
    """ Return an image of a tag shaped object containing a given text string
    and X, fixing a given height and varying the width based on the length of
    the string """
    image = _text_tag(text, **kwargs)
    img_width, img_height = image.size
    aspect = img_width / img_height
    width = int(height * aspect)
    image = image.resize((width, height), resample = Image.ANTIALIAS)
    image = force_opacity(image)
    if dimensions:
        return (image, width, height)
    else:
        return image

def x_image(height, colour = "black", background = (0, 0, 0, 0),
            bordercolour = "white"):
    image = Image.new('RGBA', (1000, 1000), color = background)
    draw = ImageDraw.Draw(image)
    rounded_line(draw, ((200, 200, 800, 800)), fill = bordercolour, width = 200)
    rounded_line(draw, ((200, 800, 800, 200)), fill = bordercolour, width = 200)
    rounded_line(draw, ((200, 200, 800, 800)), fill = colour, width = 150)
    rounded_line(draw, ((200, 800, 800, 200)), fill = colour, width = 150)

    image = image.resize((height, height), resample = Image.NEAREST)
    image = force_opacity(image)
    return image

def tick_image(height, colour = "black", background = (0, 0, 0, 0),
               bordercolour = "white"):
    image = Image.new('RGBA', (1000, 1000), color = background)
    draw = ImageDraw.Draw(image)
    rounded_line(draw, ((200, 600, 400, 800)), fill = bordercolour, width = 200)
    rounded_line(draw, ((400, 800, 800, 200)), fill = bordercolour, width = 200)
    rounded_line(draw, ((200, 600, 400, 800)), fill = colour, width = 150)
    rounded_line(draw, ((400, 800, 800, 200)), fill = colour, width = 150)

    image = image.resize((height, height), resample = Image.NEAREST)
    image = force_opacity(image)
    return image

def force_opacity(image):
    # force all translucent pixels to be fully opaque
    # this prevents an issue with anti aliasing slightly darkening the
    # background around the edges of lines and keeping it visible
    pixels = image.load()
    for px in range(image.width):
        for py in range(image.height):
            if pixels[px, py][3] > 0:
                r, g, b, a = pixels[px, py]
                pixels[px, py] = (r, g, b, 255)
    return image

if __name__ == "__main__":
    tag = text_tag("cost: £7.45", interior = "#808080",
                   text_colour = "white", x_colour = "#D3D3D3",
                   height = 250)
    tag.show()
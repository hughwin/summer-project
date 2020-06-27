import random
import bot

from PIL import Image, ImageDraw

origDimension = 1500
r = lambda: random.randint(50, 215)
rc = lambda: (r(), r(), r())
listSym = []


def create_square(border, draw, rand_colour, element, size):
    if element == int(size / 2):
        draw.rectangle(border, rand_colour)
    elif len(listSym) == element + 1:
        draw.rectangle(border, listSym.pop())
    else:
        listSym.append(rand_colour)
        draw.rectangle(border, rand_colour)


def create_invader(border, draw, size):
    x0, y0, x1, y1 = border
    square_size = (x1 - x0) / size
    rand_colors = [rc(), rc(), rc(), (0, 0, 0), (0, 0, 0), (0, 0, 0)]
    i = 1
    for y in range(0, size):
        i *= -1
        element = 0
        for x in range(0, size):
            top_left_x = x * square_size + x0
            top_left_y = y * square_size + y0
            bot_right_x = top_left_x + square_size
            bot_right_y = top_left_y + square_size
            create_square((top_left_x, top_left_y, bot_right_x, bot_right_y), draw, random.choice(rand_colors), element,
                          size)
            if element == int(size / 2) or element == 0:
                i *= -1;
            element += i


def generate_image(size, invaders, img_size):
    orig_dimension = img_size
    orig_image = Image.new('RGB', (orig_dimension, orig_dimension))
    draw = ImageDraw.Draw(orig_image)
    invader_size = orig_dimension / invaders
    padding = invader_size / size
    for x in range(0, invaders):
        for y in range(0, invaders):
            top_left_x = x * invader_size + padding / 2
            top_left_y = y * invader_size + padding / 2
            bot_right_x = top_left_x + invader_size - padding
            bot_right_y = top_left_y + invader_size - padding
            create_invader((top_left_x, top_left_y, bot_right_x, bot_right_y), draw, size)
    orig_image.save(
        "Examples/Example-" + str(size) + "x" + str(size) + "-" + str(invaders) + "-" + str(img_size) + ".jpg")
    bot.toot_image("Examples/Example-" + str(size) + "x" + str(size) + "-" + str(invaders) + "-" + str(img_size) + ".jpg")


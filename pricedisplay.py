#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function

import pygame
import requests
from argparse import ArgumentParser
import sys

size = (1920 // 2, 1080 // 2)

fonts = {} # Cache of font objects indexed by size
args = None

def fetch_location(loc):
    try:
        lines = requests.get("{}location/{}.json".format(args.address, loc)).json()
        l = []
        for sl in lines["location"]:
            unit = sl["unit"] if sl["price_for_units"] == "1.0" else "{} {}s".format(
                sl["price_for_units"], sl["unit"])
            if unit == "750.0 mls":
                unit = "bottle"
            l.append(((0xff, 0xff, 0xff), sl["line"], sl["description"],
                      "£{}/{}".format(sl["price"], unit)))
        return l
    except:
        return None

def maxwidth(font, lines):
    widths = [font.size(l)[0] for l in lines]
    return max(widths)

def getfont(size):
    global fonts
    if size not in fonts:
        fonts[size] = pygame.font.Font(
            pygame.font.match_font(",".join(args.font)), size)
    return fonts[size]

def repaint(d):
    lines = None
    while lines is None:
        lines = fetch_location(args.location)
        if lines is None:
            f = getfont(50)
            s = f.render("Network error - not up to date", True, (255, 0, 0))
            d.blit(s, (0, 0))
            pygame.display.update()
    fontsize = d.get_height() // len(lines)
    lineheight = fontsize
    widths = [width + 1]
    while True:
        f = getfont(fontsize)
        widths = [maxwidth(f, x) for x in zip(*lines)[1:]]
        if (sum(widths) + args.mincolgap * (len(widths) - 1)) <= width:
            break
        fontsize = fontsize - 1

    colgap = (width - sum(widths)) / (len(widths) - 1)
    d.fill((0, 0, 0))
    y = 0
    for l in lines:
        cols = zip(widths, l[1:])
        x = 0
        for c in cols:
            s = f.render(c[1], True, l[0])
            d.blit(s, (x, y))
            x = x + c[0] + colgap
        y = y + lineheight
    pygame.display.update()

if __name__ == "__main__":
    parser = ArgumentParser()
    aa = parser.add_argument
    aa("-m", "--fullscreen", dest="fullscreen", help="display full-screen",
       action="store_true", default=False)
    aa("-f", "--font", dest="font", help="add a font to try", action="append",
       metavar="FONTNAME", default=[])
    aa("-g", "--mincolgap", dest="mincolgap", type=int, metavar="GAP",
       default=10, help="minimum inter-column gap in pixels")
    aa("--list-fonts", dest="listfonts", action="store_true", default=False,
       help="list available fonts and exit")
    aa("-l", "--location", dest="location", default="Bar",
       help="stock line location to display")
    aa("address", help="web server base address")
    args = parser.parse_args()
    if args.listfonts:
        pygame.font.init()
        print(" ".join(pygame.font.get_fonts()))
        sys.exit(0)
    
    pygame.init()
    if args.fullscreen:
        d = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
    else:
        d = pygame.display.set_mode(size)
    width = d.get_width()

    # Update every minute
    pygame.time.set_timer(pygame.USEREVENT, 60000)
    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {}))
    finished = False
    while not finished:
        event = pygame.event.wait()
        if event.type == pygame.USEREVENT:
            repaint(d)
        elif event.type == pygame.QUIT:
            finished = True
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            finished = True
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            repaint(d)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
from argparse import ArgumentParser
import sys
from quicktill.models import *
from quicktill import td

size=(1920/2,1080/2)

fonts={} # Font objects indexed by size
args=None

def fetch_location(loc):
    lines=td.s.query(StockLine).filter(StockLine.location==loc).\
        order_by(StockLine.name).all()
    l=[]
    for sl in lines:
        if sl.capacity: continue
        if not sl.stockonsale: continue
        si=sl.stockonsale[0]
        # Colour is white for remaining>0.5
        # Blue fades out for remaining between 0.25 and 0.5
        # Green fades out for remaining between 0 and 0.25
        remaining=float(si.used/si.stockunit.size)
        red=255
        if remaining>0.25: green=255
        else: green=255*(remaining*4)
        if remaining>0.5: blue=255
        elif remaining>0.25: blue=255*((remaining-0.25)*4)
        else: blue=0
        l.append(((red,green,blue),sl.name,"%s %s %s"%(
                    si.stocktype.manufacturer,
                    si.stocktype.name,
                    si.stocktype.abvstr),
                  u"£%s/%s"%(si.stocktype.saleprice,si.stocktype.unit.name)))
    return l

def maxwidth(font,lines):
    widths=[font.size(l)[0] for l in lines]
    return max(widths)

def getfont(size):
    global fonts,font
    if size not in fonts:
        fonts[size]=pygame.font.Font(
            pygame.font.match_font(",".join(args.font)),size)
    return fonts[size]

def repaint(d):
    with td.orm_session():
        lines=fetch_location(args.location)
    fontsize=d.get_height()/len(lines)
    lineheight=fontsize
    widths=[width+1]
    while True:
        f=getfont(fontsize)
        widths=[maxwidth(f,x) for x in zip(*lines)[1:]]
        if (sum(widths)+args.mincolgap*(len(widths)-1))<=width: break
        fontsize=fontsize-1

    colgap=(width-sum(widths))/(len(widths)-1)
    d.fill((0,0,0))
    y=0
    for l in lines:
        cols=zip(widths,l[1:])
        x=0
        for c in cols:
            s=f.render(c[1],True,l[0])
            d.blit(s,(x,y))
            x=x+c[0]+colgap
        y=y+lineheight
    pygame.display.update()

if __name__=="__main__":
    parser=ArgumentParser()
    aa=parser.add_argument
    aa("-m","--fullscreen",dest="fullscreen",help="display full-screen",
       action="store_true",default=False)
    aa("-f","--font",dest="font",help="add a font to try",action="append",
       metavar="FONTNAME",default=[])
    aa("-g","--mincolgap",dest="mincolgap",type=int,metavar="GAP",default=10,
       help="minimum inter-column gap in pixels")
    aa("--list-fonts",dest="listfonts",action="store_true",default=False,
       help="list available fonts and exit")
    aa("-l","--location",dest="location",default="Bar",
       help="stock line location to display")
    aa("database",help="database connection string")
    args=parser.parse_args()
    if args.listfonts:
        pygame.font.init()
        print " ".join(pygame.font.get_fonts())
        sys.exit(0)
    td.init(args.database)
    
    pygame.init()
    if args.fullscreen:
        d=pygame.display.set_mode((0,0),pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
    else:
        d=pygame.display.set_mode(size)
    width=d.get_width()

    # Update every minute
    pygame.time.set_timer(pygame.USEREVENT,60000)
    pygame.event.post(pygame.event.Event(pygame.USEREVENT,{}))
    finished=False
    while not finished:
        event=pygame.event.wait()
        if event.type==pygame.USEREVENT:
            repaint(d)
        elif event.type==pygame.QUIT:
            finished=True
        elif event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
            finished=True
        elif event.type==pygame.KEYDOWN and event.key==pygame.K_SPACE:
            repaint(d)

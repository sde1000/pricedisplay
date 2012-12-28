#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2 as db
import pygame
from optparse import OptionParser
import sys

size=(1920/2,1080/2)

fonts={} # Font objects indexed by size
con=None
opts=None

def fetch_location(loc):
    cur=con.cursor()
    cur.execute("SELECT sl.name,si.manufacturer,si.name,si.abv,"
                "si.saleprice,si.unit,si.used/si.size AS remaining "
                "FROM stocklines sl "
                "JOIN stockonsale sos ON sos.stocklineid=sl.stocklineid "
                "JOIN stockinfo si ON si.stockid=sos.stockid "
                "WHERE sl.location=%s AND sos.stockid IS NOT NULL "
                "ORDER BY sl.name",
                (loc,))
    lines=cur.fetchall()
    l=[]
    for slname,manu,name,abv,saleprice,unit,remaining in lines:
        # Colour is white for remaining>0.5
        # Blue fades out for remaining between 0.25 and 0.5
        # Green fades out for remaining between 0 and 0.25
        remaining=float(remaining)
        red=255
        if remaining>0.25: green=255
        else: green=255*(remaining*4)
        if remaining>0.5: blue=255
        elif remaining>0.25: blue=255*((remaining-0.25)*4)
        else: blue=0
        l.append(((red,green,blue),slname,"%s %s %s%%"%(manu,name,abv),
                  u"£%s/%s"%(saleprice,unit)))
    return l

def maxwidth(font,lines):
    widths=[font.size(l)[0] for l in lines]
    return max(widths)

def getfont(size):
    global fonts,font
    if size not in fonts:
        fonts[size]=pygame.font.Font(
            pygame.font.match_font(",".join(opts.font)),size)
    return fonts[size]

def repaint(d):
    lines=fetch_location("Bar")
    fontsize=d.get_height()/len(lines)
    lineheight=fontsize
    widths=[width+1]
    while True:
        f=getfont(fontsize)
        widths=[maxwidth(f,x) for x in zip(*lines)[1:]]
        if (sum(widths)+opts.mincolgap*(len(widths)-1))<=width: break
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
    pa=OptionParser("usage: %prog [options] database-connection-string")
    ao=pa.add_option
    ao("-m","--fullscreen",dest="fullscreen",help="display full-screen",
       action="store_true",default=False)
    ao("-f","--font",dest="font",help="add a font to try",action="append",
       type="string",metavar="FONTNAME",default=[])
    ao("-g","--mincolgap",dest="mincolgap",type="int",metavar="GAP",default=10,
       help="minimum inter-column gap in pixels")
    ao("-l","--list-fonts",dest="listfonts",action="store_true",default=False,
       help="list available fonts and exit")
    (opts,args)=pa.parse_args()
    if opts.listfonts:
        pygame.font.init()
        print " ".join(pygame.font.get_fonts())
        sys.exit(0)
    if len(args)!=1:
        pa.print_usage()
        sys.exit(1)

    con=db.connect(args[0])
    
    pygame.init()
    if opts.fullscreen:
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

#!/usr/bin/python

import os
import sys
import argparse

from lxml.cssselect import CSSSelector as css
from lxml.html import builder as E
from lxml import etree

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--start', '-s', default='css:body',
            help='Selector identifying element from which to start looking for headers.')
    p.add_argument('--toc', '-t', default='.//p[text()="[[TOC]]"]',
            help='Selector identifying element that will be replaced with TOC.')
    p.add_argument('--list-tag', '-l', default='ol',
            help='Element type for lists (generally "ul" or "ol").')
    p.add_argument('--skip-first-header', '-S', action='store_true',
            help='Ignore the first header in the document.')
    p.add_argument('--debug', action='store_true')
    p.add_argument('input', nargs='?')
    p.add_argument('output', nargs='?')
    return p.parse_args()

def selector (s):
    if s.startswith('css:'):
        return css(s[4:]).path
    elif s.startswith('xpath:'):
        return s[6:]
    else:
        return s

def main():
    opts = parse_args()

    opts.toc = selector(opts.toc)
    opts.start = selector(opts.start)

    if opts.debug:
        print >>sys.stderr, 'toc xpath:', opts.toc
        print >>sys.stderr, 'start xpath:', opts.start

    if opts.input:
        infd = open(opts.input)
    else:
        infd = sys.stdin

    doc = etree.HTML(infd.read())

    if opts.start:
        matches = doc.xpath(opts.start)

        if not matches:
            print >>sys.stderr, 'Failed to locate start element.'
            sys.exit(1)

        start = matches[0]
    else:
        start = doc

    matches = start.xpath(opts.toc)
    if not matches:
        print >>sys.stderr, 'Failed to locate target element.'
        sys.exit(1)
    target = matches[0]

    sel = css('h1,h2,h3,h4')
    id = 1
    toc = etree.Element(opts.list_tag)
    cur = toc
    lasthdrlevel = 1
    first = True
    for hdr in start.xpath(sel.path):
        if opts.skip_first_header and first:
            first=False
            continue

        if opts.debug:
            print >>sys.stderr, 'element:', hdr.tag, hdr.text

        hdrlevel = int(hdr.tag[1:])
        if hdrlevel > lasthdrlevel:
            new = etree.Element(opts.list_tag)
            cur.append(new)
            cur = new
        elif hdrlevel < lasthdrlevel:
            cur = cur.getparent()
        lasthdrlevel = hdrlevel

        hdrid = 'id%d' % id
        id += 1

        hdr.append(E.A(hdr.text, name=hdrid))
        cur.append(E.LI(
            E.A(hdr.text, href='#%s' % hdrid)))

        if opts.debug:
            print >>sys.stderr, 'TOC:'
            print >>sys.stderr, etree.tostring(toc)
            print >>sys.stderr, 'CUR:'
            print >>sys.stderr, etree.tostring(cur)

        hdr.text = ''

    target.getparent().replace(target, E.DIV(toc, id='toc'))

    if opts.output:
        outfd = open(opts.output, 'w')
    else:
        outfd = sys.stdout

    print >>outfd, etree.tostring(doc, pretty_print=True, method='html')

if __name__ == '__main__':
    main()


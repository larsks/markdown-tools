#!/usr/bin/python

import os
import sys
import argparse

from lxml.cssselect import CSSSelector as css
from lxml.html import builder as E
from lxml import etree

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--css', action='store_true')
    p.add_argument('--start', '-s', default='/html/body')
    p.add_argument('--toc', '-t', default='.//div[@id="toc"]')
    p.add_argument('--list-tag', '-l', default='ol')
    p.add_argument('--skip-first-header', '-S', action='store_true')
    p.add_argument('input', nargs='?')
    p.add_argument('output', nargs='?')
    return p.parse_args()

def selector (s):
    if not s.startswith('css:'):
        return s

    return css(s[4:]).path

def main():
    opts = parse_args()

    if opts.input:
        infd = open(opts.input)
    else:
        infd = sys.stdin

    doc = etree.HTML(infd.read())

    if opts.start:
        if opts.css:
            opts.start = css(opts.start).path

        matches = doc.xpath(opts.start)

        if not matches:
            print >>sys.stderr, 'Failed to locate start element.'
            sys.exit(1)

        start = matches[0]

    else:
        start = doc

    if opts.css:
        opts.toc = css(opts.css).path

    matches = start.xpath(opts.toc)
    if not matches:
        print >>sys.stderr, 'Failed to locate target element.'
        sys.exit(1)
    target = matches[0]

    sel = css('h1,h2,h3,h4')
    id = 1
    toc = etree.Element(opts.list_tag)
    lasthdrlevel = 1
    first = True
    for hdr in start.xpath(sel.path):

        if opts.skip_first_header and first:
            first=False
            continue

        hdrlevel = int(hdr.tag[1:])
        if hdrlevel > lasthdrlevel:
            new = etree.Element(opts.list_tag)
            toc.append(new)
            toc = new
        elif hdrlevel < lasthdrlevel:
            toc = toc.getparent()
        lasthdrlevel = hdrlevel

        hdrid = 'id%d' % id

        hdr.append(E.A(hdr.text, name=hdrid))
        toc.append(E.LI(
            E.A(hdr.text, href='#%s' % hdrid)))

        hdr.text = ''

        id += 1

    target.append(toc)

    if opts.output:
        outfd = open(opts.output, 'w')
    else:
        outfd = sys.stdout

    print >>outfd, etree.tostring(doc, pretty_print=True, method='html')

if __name__ == '__main__':
    main()


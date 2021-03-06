from __future__ import absolute_import, unicode_literals
from future.builtins import chr, int

try:
    from html.parser import HTMLParser, HTMLParseError
    from html.entities import name2codepoint
except ImportError:         # Python 2
    from HTMLParser import HTMLParser, HTMLParseError
    from htmlentitydefs import name2codepoint

import re


SELF_CLOSING_TAGS = ['br', 'img']


def decode_entities(html):
    """
    Remove HTML entities from a string.
    Adapted from http://effbot.org/zone/re-sub.htm#unescape-html
    """
    def decode(m):
        html = m.group(0)
        if html[:2] == "&#":
            try:
                if html[:3] == "&#x":
                    return chr(int(html[3:-1], 16))
                else:
                    return chr(int(html[2:-1]))
            except ValueError:
                pass
        else:
            try:
                html = chr(name2codepoint[html[1:-1]])
            except KeyError:
                pass
        return html
    return re.sub("&#?\w+;", decode, html.replace("&amp;", "&"))


def thumbnails(html):
    """
    Given a HTML string, converts paths in img tags to thumbnail
    paths, using Mezzanine's ``thumbnail`` template tag. Used as
    one of the default values in the ``RICHTEXT_FILTERS`` setting.
    """
    from django.conf import settings
    from html5lib.treebuilders import getTreeBuilder
    from html5lib.html5parser import HTMLParser
    from mezzanine.core.templatetags.mezzanine_tags import thumbnail

    dom = HTMLParser(tree=getTreeBuilder("dom")).parse(html)
    for img in dom.getElementsByTagName("img"):
        src = img.getAttribute("src")
        width = img.getAttribute("width")
        height = img.getAttribute("height")
        if src and width and height:
            src = settings.MEDIA_URL + thumbnail(src, width, height)
            img.setAttribute("src", src)
    nodes = dom.getElementsByTagName("body")[0].childNodes
    return "".join([node.toxml() for node in nodes])


class TagCloser(HTMLParser):
    """
    HTMLParser that closes open tags. Takes a HTML string as its first
    arg, and populate a ``html`` attribute on the parser with the
    original HTML arg and any required closing tags.
    """

    def __init__(self, html):
        HTMLParser.__init__(self)
        self.html = html
        self.tags = []
        try:
            self.feed(self.html)
        except HTMLParseError:
            pass
        else:
            self.html += "".join(["</%s>" % tag for tag in self.tags])

    def handle_starttag(self, tag, attrs):
        if(tag not in SELF_CLOSING_TAGS):
            self.tags.insert(0, tag)

    def handle_endtag(self, tag):
        try:
            self.tags.remove(tag)
        except ValueError:
            pass

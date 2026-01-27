from typing import Any
import html5lib

def get_parser(treebuilder='etree'):
    return html5lib.HTMLParser(treebuilder=treebuilder)

import sublime
import sublime_plugin
import re

DEFINITION_KEY = 'footnote-definitions'
REFERENCE_KEY = 'footnote-references'
REFERENCE_REGEX = r'\[(\d+)\]\_'
DEFINITION_REGEX = r"^\.\.\s\[(\d+)\]"


def __get_id(txt):
    return re.findall(r'\d+', txt)[0]

def __get_footnote_identifiers(view):
    ids = get_footnote_references(view).keys()
    list(ids).sort()
    return ids

def __get_last_footnote_marker(view):
    ids = sorted([int(a) for a in __get_footnote_identifiers(view) if a.isdigit()])
    if len(ids):
        return int(ids[-1])
    else:
        return 0

def get_footnote_references(view):
    ids = {}
    for ref in view.get_regions(REFERENCE_KEY):
        # [01]_ pattern could be part of a footnote definition rather than an inline footnote reference
        # i.e. it could be ..[1]_ footnote text
        if not re.match(DEFINITION_REGEX, view.substr(view.line(ref))):
            # we now know the 'ref' is not part of a footnote definition
            # we can safely assume it's a footnote reference
            id = __get_id(view.substr(ref)) # extract the number
            if id in ids:
                ids[id].append(ref)
            else:
                ids[id] = [ref]
    return ids # dict of { "num": Region } for footnote refs in the view

def get_footnote_definition_markers(view):
    ids = {}
    for defn in view.get_regions(DEFINITION_KEY):
        id = __get_id(view.substr(defn))
        ids[id] = defn
    # print(f'footnote def markers: = {ids}')
    return ids

def get_next_footnote_marker(view):
    return __get_last_footnote_marker(view) + 1

def is_footnote_definition(view):
    line = view.substr(view.line(view.sel()[-1]))
    # print(f'searching line: {line} is footnote def = {re.match(DEFINITION_REGEX, line)}')
    return re.match(DEFINITION_REGEX, line)

def is_footnote_reference(view):
    refs = view.get_regions(REFERENCE_KEY)
    for ref in refs:
        # print(f'sel region = {view.sel()[0]}')
        if ref.contains(view.sel()[0]):
            return True
    return False

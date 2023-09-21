import sublime, sublime_plugin, re, os, sys, string
from collections import namedtuple
import json
import xml.etree.ElementTree as ET


from .utils.constants import pluginEnv, pluginSettingsGovernor
from .utils import footnotesUtils as fu
from .utils import listsUtils as slu
from .utils.textcommandUtils import BaseBlockCommand

#saltydogSTARTsaltydogSTARTsaltydogSTARTsaltydogSTARTsaltydogSTARTsaltydogSTARTsaltydogSTARTsaltydogSTARTsaltydogSTART

try:
    from saltydog.saltydog import pluginCentraliser, runSafeSubprocess, testViewForScopes
except:
    from .utils.saltydog import pluginCentraliser, runSafeSubprocess, testViewForScopes

pluginCentral = None

if int(sublime.version()) >= 3114:

    # Clear module cache to force reloading all modules of this package.
    prefix = __package__ + "."  # don't clear the base package
    for module_name in [
        module_name
        for module_name in sys.modules
        if module_name.startswith(prefix) and module_name != __name__
    ]:
        del sys.modules[module_name]
    prefix = None

    # Import public API classes
    # from .core.command import MyTextCommand
    # from .core.events import MyEventListener

    def plugin_loaded():
        """
        Initialize plugin:
        This module level function is called on ST startup when the API is ready. 
        """
        # print(f'{pluginEnv["pluginName"]} (re)loaded')
        global pluginCentral
        pluginCentral = pluginCentraliser(pluginSettingsGovernor, pluginEnv, defaultPluginName=__package__)
        # print(f'{pluginCentral.pluginName} settings initialised')
        
    def plugin_unloaded():
        """
        This module level function is called just before the plugin is unloaded.
        Complete tasks.
        Cleanup package caches.
        Exit threads.
        """
        # print(f'{pluginEnv["pluginName"]} unloaded')

else:
    raise ImportWarning(f"The {pluginEnv.get('pluginName', __package__)} plugin doesn't work with Sublime Text versions prior to 3114")
        
class SaltyDogDynamicProjectSettingsUpdater(sublime_plugin.EventListener):
    def on_load_project(self, window):
        if pluginCentral is not None:
            pluginCentral.newProjectHook(window)
    def on_activated(self, view):
        if pluginCentral is not None:
            pluginCentral.newViewHook(view)

#saltydogENDsaltydogENDsaltydogENDsaltydogENDsaltydogENDsaltydogENDsaltydogENDsaltydogENDsaltydogEND

# class InsertMySnippetStrCommand(sublime_plugin.TextCommand):
#     snippetStr = ""

#     def run(self, edit):
#         global pluginCentral
#         if pluginCentral.allowCommandsToRun():
#             if snippetStr:
#                 self.view.run_command('insert_snippet', {'contents': self.snippetStr})

# class InsertMySnippetFileCommand(sublime_plugin.TextCommand):
#     snippetFile = ""

#     def run(self, edit):
#         global pluginCentral
#         if pluginCentral.allowCommandsToRun():
#             if snippetFile:
#                 self.view.run_command("insert_snippet", { "name": self.snippetFile })

# class WrapSelectionAsRoleCommand(InsertMySnippetCommand):
#     def description(self):
#         scopeOrNot = [' (No Scope)', ''][self.is_enabled()]
#         return f'Apply reSt :role: Syntax{scopeOrNot}'

#     def is_enabled(self):
#         return testViewForScopes(self.view, ["text.restructuredtext"])

#     def run(self, edit):
#         global pluginCentral
#         if not pluginCentral.allowCommandsToRun():
#             return
#         self.view.run_command('insert_snippet', {'contents': ":$1:`$SELECTION`"})

# class WrapSelectionAsRoleDropdownCommand(sublime_plugin.TextCommand):

#     def description(self):
#         scopeOrNot = [' (No Scope)', ''][self.is_enabled()]
#         return f'Select reSt :role: To Apply{scopeOrNot}'

#     def is_enabled(self):
#         return testViewForScopes(self.view, ["text.restructuredtext"])

#     def onQuickPanelSelectionMade(self, index):
#         if not index < 0: # index of -1 = noop; nothing was selected, e.g. the user pressed escape
#             # pluginCentral.msgBox(f'selected = {self.roleDetails[index][2]}')
#             self.view.run_command('insert_snippet', {'contents': self.roleDetails[index][2]})
    
#     def run(self, edit):
#         global pluginCentral
#         if not pluginCentral.allowCommandsToRun():
#             return
#         self.roleDetails = pluginCentral.settingsAsDict()["roleDetails"]
#         self.quickPanelList = []
#         for item in self.roleDetails:
#             quickPanelItem = sublime.QuickPanelItem(
#                     trigger=item[0],
#                     details=item[1],
#                     # annotation='',
#                     kind=sublime.KIND_SNIPPET
#             )
#             self.quickPanelList.append(quickPanelItem)
#         sublime.active_window().show_quick_panel(
#             self.quickPanelList, 
#             self.onQuickPanelSelectionMade,
#             placeholder="Choose reSt :role: to apply:"
#         )

class InsertSnippetsFromDirCommand(sublime_plugin.TextCommand):
    snippetDirs = () # tuple of strings in format 'Packages/PluginName/snippetdir'

    def onQuickPanelSelectionMade(self, index):
        if not index < 0: # index of -1 = noop; nothing was selected, e.g. the user pressed escape
            # pluginCentral.msgBox(f'selected = {self.snippetStrList[index]}')
            self.view.run_command('insert_snippet', {'contents': self.snippetStrList[index]})

    def run(self, edit):
        global pluginCentral
        if not pluginCentral.allowCommandsToRun():
            return
        if not self.snippetDirs:
            return
        allSnippetPaths = sublime.find_resources("*.sublime-snippet")
        targetSnippetPaths = [ p for p in allSnippetPaths if p.startswith(self.snippetDirs)]
        self.snippetStrList = []
        snippetPanelList = []
        xmlErrorCount = 0
        for s in targetSnippetPaths:
            snippet        = sublime.load_resource(s)
            try:
                tree           = ET.fromstring(snippet)
            except Exception as exxy:
                print(f'XML Error in snippet resource: {str(s)}\n >> {str(exxy)}')
                xmlErrorCount += 1
                continue
            name           = tree.findtext('description')
            anyTabTrigger  = tree.findtext('tabTrigger')
            tabTrigger     = [f'trig:{anyTabTrigger}', ''][anyTabTrigger is None]
            content        = tree.findtext('content')
            if content.startswith('\n'):
                content = content[1:]
            self.snippetStrList.append(content)
            snippetPanelItem = sublime.QuickPanelItem(
                    trigger=name,
                    # details='',
                    annotation=tabTrigger,
                    kind=sublime.KIND_SNIPPET
            )
            snippetPanelList.append(snippetPanelItem)
        if xmlErrorCount > 0:
            pluginCentral.status_message(f'{xmlErrorCount} snippets excluded due to XML errors (see console for details)')
        # self.quickPanelList = []
        # for item in self.roleDetails:
        if snippetPanelList:
            sublime.active_window().show_quick_panel(
                snippetPanelList, 
                self.onQuickPanelSelectionMade,
                placeholder="Choose snippet to insert::"
            )
        else:
            pluginCentral.status_message(f'Command Void as No valid snippet files found in {self.snippetDirs}')


class InsertRoleSnippetCommand(InsertSnippetsFromDirCommand):
    snippetDirs = (f'Packages/{__package__}/Snippets/reStRoles',
                   f'Packages/User/{__package__}/Snippets/reStRoles')


class InsertUserDefinedSnippetCommand(InsertSnippetsFromDirCommand):
    snippetDirs = (f'Packages/User/{__package__}')


class ConvertTextToRefLabelCommand(sublime_plugin.TextCommand):
    """
    Convert selection(s) into reSt reference label format:
    e.g. [My Textual Title] >> .. _my_textual_title
    Designed for use with reSt Titles which can then be used as references
    """

    # def description(self):
    #     scopeOrNot = [' (No Scope)', ''][self.is_enabled()]
    #     return f'Convert Selection To reSt Ref Target{scopeOrNot}'

    # def is_enabled(self):
    #     return testViewForScopes(self.view, ["text.restructuredtext"])

    def run(self, edit):
        def str_from_title(title):
            translator = str.maketrans('', '', string.punctuation)
            barestr = title.translate(translator).strip().lower()
            return ".. _{}:\n\n".format(re.sub(r"\s+", '_', barestr))

        # Main:
        # Get selection(s)
        global pluginCentral
        if not pluginCentral.allowCommandsToRun():
            return
        sel = self.view.sel();
        for s in sel:       
            if s.empty(): # expand to full line a cursor with no selection
                s = self.view.full_line(s)
            seltext = self.view.substr(s)
            new_ref_anchor = str_from_title(seltext)
            if new_ref_anchor:
                self.view.replace(edit, s, new_ref_anchor)      


#footnotesSTARTfootnotesSTARTfootnotesSTARTfootnotesSTARTfootnotesSTARTfootnotesSTARTfootnotesSTART

class Footnotes(sublime_plugin.EventListener):
    def update_footnote_data(self, view):
        view.add_regions(fu.REFERENCE_KEY,
                         view.find_all(fu.REFERENCE_REGEX),
                         '', 'cross',
                         )
        view.add_regions(fu.DEFINITION_KEY,
                         view.find_all(fu.DEFINITION_REGEX),
                         '',
                         'cross',
                         )

    def on_modified(self, view):
        self.update_footnote_data(view)

    def on_load(self, view):
        self.update_footnote_data(view)


class MagicFootnotesCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if (fu.is_footnote_definition(self.view)):
            self.view.run_command('go_to_footnote_reference')
        elif (fu.is_footnote_reference(self.view)):
            self.view.run_command('go_to_footnote_definition')
        else:
            self.view.run_command('insert_footnote')

    def is_enabled(self):
        return bool(self.view.sel())

    def description(self):
        return 'Savvy Footnote Nav/Insert'

class InsertFootnoteCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        selList = self.view.sel()
        if not len(selList) == 1:
            pluginCentral.status_message('Command is Void (multiple cursors)')
            return
        startloc = self.view.sel()[-1].end()
        markernum = fu.get_next_footnote_marker(self.view)
        if bool(self.view.size()): # the view has text?
            # find the next space|eol, in case we've tried to insert a footnote ref mid-word
            targetloc = self.view.find('(\s|$)', startloc).begin()
        else:
            targetloc = 0
        self.view.insert(edit, targetloc, '[%s]_' % markernum)
        # append the initial syntax of the footnote definition at the end of the file
        self.view.insert(edit, self.view.size(), '\n.. [%s] ' % markernum)
        self.view.sel().clear() # clear current cursor
        self.view.sel().add(sublime.Region(self.view.size())) # put cursor at eof
        self.view.show(self.view.size()) # make eof visible on screen

class MarkFootnotes(sublime_plugin.EventListener):
    def update_footnote_data(self, view):
        if view.syntax() is not None:
            if view.syntax().scope == "text.restructuredtext":
                # print(f'updating footnotes regions: File={view.file_name()}')
                view.add_regions(fu.REFERENCE_KEY, view.find_all(fu.REFERENCE_REGEX), '', 'cross', sublime.HIDDEN)
                view.add_regions(fu.DEFINITION_KEY, view.find_all(fu.DEFINITION_REGEX), '', 'cross', sublime.HIDDEN)
                # print(f'Footnote Ref Regions: {view.get_regions(fu.REFERENCE_KEY)}')
                # print(f'Footnote Def Regions: {view.get_regions(fu.DEFINITION_KEY)}')

    def on_modified(self, view):
        self.update_footnote_data(view)

    def on_activated(self, view):
        self.update_footnote_data(view)


class GoToFootnoteReferenceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        selList = self.view.sel()
        if not len(selList) == 1:
            pluginCentral.status_message('Command is Void (multiple cursors)')
            return
        match = fu.is_footnote_definition(self.view)
        if not match:
            pluginCentral.status_message('Command is Void (cursor must be in first line of footnote definition)')
            return
        refs = fu.get_footnote_references(self.view)
        if not refs:
            pluginCentral.status_message('Command is Void (document contains no footnote references)')
            return
        target = match.groups()[0]
        if not target:
            pluginCentral.status_message('Command is Void (footnote error - cannot find a number in the footnote definition)')
            return
        if not target in refs:
            pluginCentral.status_message(f'Command is Void (footnote error - reference for footnote #{target} does not exist.)')
            return
        if len(refs[target]) > 1:
            pluginCentral.status_message(f'Info: Document contains {len(refs[target])} references to footnote #{target}.')

        note = refs[target][0] # get first ref (nearest start of page), there may be many refs
        point = sublime.Region(note.end(), note.end())
        self.view.sel().clear()
        self.view.sel().add(point)
        self.view.show(note)


class GoToFootnoteDefinitionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        defs = fu.get_footnote_definition_markers(self.view)
        selList = self.view.sel()
        cursorRegion = selList[0]
        refRegions = self.view.get_regions(fu.REFERENCE_KEY)

        if not len(selList) == 1:
            pluginCentral.status_message('Command is Void (multiple cursors)')
            return
        if not defs or not refRegions:
            pluginCentral.status_message('Command is Void (no footnote pairings in document)')
            return 

        target = None
        cursorRegion = selList[0]

        for region in refRegions:
            # fuzzyHitRegion expanded to one character either side of footnote ref region
            # i.e. ·[X]_·   so a 'close by' cursor is recognised
            if region.a < region.b:
                fuzzyHitRegion = sublime.Region(region.a -1, region.b + 1)
            else:
                fuzzyHitRegion = sublime.Region(region.a +1, region.b - 1)
            if cursorRegion.intersects(fuzzyHitRegion):
                # get footnote number from region string
                target = self.view.substr(region)[1:-2]
                break

        if not target:
            pluginCentral.status_message('Command is Void (cursor not in footnote reference)')
        elif target not in defs:
            pluginCentral.error_message((f'Cannot navigate to footnote definition number {target}, as it '
                'does not exist. Please ensure your footnote references match your footnote definitions, numbers wise.'))
        else:
            self.view.sel().clear()
            point = defs[target].end() + 1
            ref = sublime.Region(point, point)
            self.view.sel().add(ref)
            self.view.show(defs[target])

#footnotesENDfootnotesENDfootnotesENDfootnotesENDfootnotesENDfootnotesENDfootnotesEND

#simpleFormatSTARTsimpleFormatSTARTsimpleFormatSTARTsimpleFormatSTARTsimpleFormatSTART

class SurroundCommand(sublime_plugin.TextCommand):
    """
    Base class to surround the selection with text.
    """
    surround = ''

    def run(self, edit):
        print(f'running surroundcommand with [{self.surround}]')
        try:
            formatToRstSyntax = self.view.syntax().scope == "text.restructuredtext"
        except:
            formatToRstSyntax = False
        if formatToRstSyntax:
            for sel in self.view.sel():
                if sel.empty():
                    # insert single 'surround' character if selection is an empty cursor
                    self.view.insert(edit, sel.begin(), self.surround)
                else:
                    # insert 'surround' character after+before selection (without changing selected text)
                    self.view.insert(edit, sel.end(), self.surround)
                    self.view.insert(edit, sel.begin(), self.surround)
        else:
            # this may not ever run as context menu and key binds should only be enabled for reSt syntax
            # Simply replace all sels with a single 'surround' char (non-special, default editing behaviour)
            for sel in self.view.sel():
                if sel.empty():
                    self.view.insert(edit, sel.begin(), self.surround)
                else:
                    insertPoint = sel.begin()
                    self.view.erase(edit, sel)
                    self.view.insert(edit, insertPoint, self.surround)


class MenuVisibleForRstCommand(sublime_plugin.TextCommand):
    def description(self):
        return "reStAssured"

    def is_visible(self):
        try:
            enableMe = self.view.syntax().scope == "text.restructuredtext"
        except:
            enableMe = False
        return enableMe


class StrongEmphasisCommand(SurroundCommand):
    surround = "**"

class EmphasisCommand(SurroundCommand):
    surround = "*"

class LiteralCommand(SurroundCommand):
    surround = "``"

class BackTickCommand(SurroundCommand):
    surround = "`"

class SubstitutionCommand(SurroundCommand):
    surround = "|"

#simpleFormatENDsimpleFormatENDsimpleFormatENDsimpleFormatENDsimpleFormatEND

#headersSTARTheadersSTARTheadersSTARTheadersSTARTheadersSTARTheadersSTARTheadersSTART

# reference:
#   http://docutils.sourceforge.net/docs/ref/rst/restructuredtext.html#sections
ADORNMENTS = r"""[!\"#$%&'\\()*+,\-./:;<=>?@\[\]\^_`{|}~]"""
PATTERN_RE = re.compile(r"^(%s*)\n(.+)\n(%s+)" % (ADORNMENTS, ADORNMENTS), re.MULTILINE)

Header = namedtuple('Header', "level start end adornment title raw idx")


class RstHeaderTree(object):
    # based on sphinx's header conventions
    DEFAULT_HEADERS = '** = - ^ " + ~ # \' :'.split()

    def __init__(self, text):
        # add a ficticius break as first line
        # to allow catching a very first header without overline.
        # This imply any position returned (Header.start, Header.end)
        # must be decremented one character

        self.headers = self._parse('\n' + text)
        self._text_length = len(text)

    def _parse(self, text):
        """
        Given a chunk of restructuredText, returns a list of tuples
        (level, start, end, adornment, title, raw) for each header found.


        level: int (zero-based). the "weight" of the header.
        start: index where the header starts
        end: index where the header ends
        adornment: one (just underlined) or two char
                    (over and underline) string
                    that represent the adornment,
        title: the parsed title
        raw : the raw parsed header text, including breaks.

        """

        candidates = PATTERN_RE.findall(text)
        headers = []
        levels = []
        idx = 0

        for over, title, under in candidates:
            # validate.
            if ((over == '' or over == under) and len(under) >= len(title)
                    and len(set(under)) == 1):
                # encode the adornment of the header to calculate its level
                adornment = under[0] * (2 if over else 1)
                if adornment not in levels:
                    levels.append(adornment)
                level = levels.index(adornment)
                raw = (over + '\n' if over else '') + title + '\n' + under
                start = text.find(raw) - 1  # see comment on __init__
                end = start + len(raw)
                h = Header(level, start, end, adornment, title, raw, idx)
                idx += 1
                headers.append(h)
        return headers

    def belong_to(self, pos):
        """
        given a cursor position, return the deeper header
        that contains it
        """
        match = []
        for h in self.headers:
            start, end = self.region(h)
            if start <= pos <= end:
                match.append(h)
        try:
            return sorted(match, key=lambda h: h.level, reverse=True)[0]
        except IndexError:
            return None

    def region(self, header):
        """
        determines the (start, end) region under the given header
        A region ends when a header of the same or higher level
        (i.e lower number) is found or at the EOF
        """

        try:
            index = self.headers.index(header)
        except ValueError:
            return

        start = header.start
        if index == len(self.headers) - 1:     # last header
            return (start, self._text_length)

        for next_h in self.headers[index + 1:]:
            if next_h.level <= header.level:
                return (start, next_h.start - 1)

        return (start, self._text_length)

    def _index(self, header, same_or_high=False):
        """
        helper method that returns the absolute index
        of the header in the tree or a filteredr tree
        If same_or_high is true, only move to headline with the same level
        or higher level.

        returns (index, headers)
        """
        if same_or_high:
            headers = [h for h in self.headers
                       if h.level <= header.level]
        else:
            headers = self.headers[:]
        return headers.index(header), headers

    def next(self, header, same_or_high=False):
        """
        given a header returns the closer header
        (down direction)
        """
        index, headers = self._index(header, same_or_high)
        try:
            return headers[index + 1]
        except IndexError:
            return None

    def prev(self, header, same_or_high=False, offset=-1):
        """same than next, but in reversed direction
        """
        index, headers = self._index(header, same_or_high)
        if index == 0:
            return None
        return headers[index + offset]

    def levels(self):
        """ returns the heading adornment map"""
        _levels = RstHeaderTree.DEFAULT_HEADERS.copy()
        for h in self.headers:
            _levels[h.level] = h.adornment
        levels = []
        for adornment in _levels:
            if adornment not in levels:
                levels.append(adornment)
        for adornment in RstHeaderTree.DEFAULT_HEADERS:
            if adornment not in levels:
                if len(adornment) == 2:
                    levels.insert(0, adornment)
                else:
                    levels.append(adornment)
        return levels

    @classmethod
    def make_header(cls, title, adornment, force_overline=False):
        title = title.rstrip()
        title_lenght = len(title.lstrip())
        indent_lenght = len(title) - title_lenght
        title_lenght += len(''.join(re.compile(u"[\u4e00-\u9fa5]+").findall(title)))
        title_lenght += len(''.join(re.compile(u"[\uac00-\ud7af]+").findall(title)))
        strike = adornment[0] * (title_lenght + indent_lenght * 2)
        if force_overline or len(adornment) == 2:
            result = strike + '\n' + title + '\n' + strike + '\n'
        else:
            result = title + '\n' + strike + '\n'
        return result


class HeaderChangeLevelCommand(sublime_plugin.TextCommand):
    """
    increase or decrease the header level,
    The level markup is autodetected from the document,
    and use sphinx's convention by default.
    """
    views = {}
    movingOnUp = True

    # def run(self, edit, offset=-1):
    def run(self, edit):
        offset = [1, -1][self.movingOnUp]
        vid = self.view.id()
        HeaderChangeLevelEvent.listen.pop(vid, None)

        cursor_pos = self.view.sel()[0].begin()
        region = sublime.Region(0, self.view.size())
        tree = RstHeaderTree(self.view.substr(region))

        parent = tree.belong_to(cursor_pos)

        is_in_header = parent.start <= cursor_pos <= parent.end
        if not is_in_header:
            return

        idx, levels = HeaderChangeLevelCommand.views.get(vid, (None, None))
        if idx != parent.idx:
            levels = tree.levels()
            HeaderChangeLevelCommand.views[vid] = (parent.idx, levels)

        try:
            level = levels.index(parent.adornment)
            if level + offset < 0:
                return
            adornment = levels[level + offset]
        except IndexError:
            return

        new_header = RstHeaderTree.make_header(parent.title, adornment)
        hregion = sublime.Region(parent.start, parent.end + 1)

        try:
            self.view.replace(edit, hregion, new_header)
        finally:
            def callback():
                HeaderChangeLevelEvent.listen[vid] = True
            sublime.set_timeout(callback, 0)

class HeaderChangeLevelUpCommand(HeaderChangeLevelCommand):
    movingOnUp = True


class HeaderChangeLevelDownCommand(HeaderChangeLevelCommand):
    movingOnUp = False


class HeaderChangeLevelEvent(sublime_plugin.EventListener):
    listen = {}

    def on_modified(self, view):
        vid = view.id()
        if HeaderChangeLevelEvent.listen.get(vid):
            del HeaderChangeLevelCommand.views[vid]
            del HeaderChangeLevelEvent.listen[vid]


class SkipToHeaderBaseCommand(sublime_plugin.TextCommand):
    # briefly inspired on the code of Muchenxuan Tong in
    # https://github.com/demon386/SmartMarkdown
    forward = True
    same_or_higher = False

    def run(self, edit):
        """Move between headlines, forward or backward.

        If self.same_or_higher is true, only move to headline with the same level
        or higher level.

        """
        cursor_pos = self.view.sel()[0].begin()
        region = sublime.Region(0, self.view.size())
        tree = RstHeaderTree(self.view.substr(region))
        parent = tree.belong_to(cursor_pos)

        if self.forward:
            h = tree.next(parent, self.same_or_higher)
        else:
            is_in_header = parent.start <= cursor_pos <= parent.end
            offset = -1 if is_in_header else 0
            h = tree.prev(parent, self.same_or_higher, offset)
        if h:
            self.jump_to(h.end - len(h.raw.split('\n')[-1]) - 1)

    def jump_to(self, pos):
        region = sublime.Region(pos, pos)
        self.view.sel().clear()
        self.view.sel().add(region)
        self.view.show(region)

class JumpForwardSameLevelCommand(SkipToHeaderBaseCommand):
    forward = True
    same_or_higher = True

class JumpForwardAnyLevelCommand(SkipToHeaderBaseCommand):
    forward = True
    same_or_higher = False

class JumpBackSameLevelCommand(SkipToHeaderBaseCommand):
    forward = False
    same_or_higher = True

class JumpBackAnyLevelCommand(SkipToHeaderBaseCommand):
    forward = False
    same_or_higher = False


class HeaderFoldingOnOffCommand(sublime_plugin.TextCommand):
    """
    Smart folding is used to fold / unfold headline at the point.
    """
    def run(self, edit):

        cursor_pos = self.view.sel()[0].begin()
        region = sublime.Region(0, self.view.size())
        tree = RstHeaderTree(self.view.substr(region))
        parent = tree.belong_to(cursor_pos)
        is_in_header = parent.start <= cursor_pos <= parent.end
        if is_in_header:
            start, end = tree.region(parent)
            start += len(parent.raw) + 1
            region = sublime.Region(start, end)
            if any([i.contains(region) for i in
                    self.view.folded_regions()]):
                self.view.unfold(region)
            else:
                self.view.fold(region)
        else:
            for r in self.view.sel():
                self.view.insert(edit, r.a, '\t')
                self.view.show(r)


class HeaderMarkingsFillerCommand(BaseBlockCommand):
    def run(self, edit):
        for region in self.view.sel():
            region, lines, indent = self.get_block_bounds()
            head_lines = len(lines)
            adornment_char = lines[-1][0]

            if (head_lines not in (2, 3) or
                    head_lines == 3 and lines[-3][0] != adornment_char):
                # invalid header
                return

            title = lines[-2]
            force_overline = head_lines == 3
            result = RstHeaderTree.make_header(title, adornment_char, force_overline)
            self.view.replace(edit, region, result)

#headersENDheadersENDheadersENDheadersENDheadersENDheadersENDheadersENDheadersENDheadersEND

#smartlistsSTARTsmartlistsSTARTsmartlistsSTARTsmartlistsSTARTsmartlistsSTARTsmartlistsSTART

class SmartListCommand(BaseBlockCommand):

    def run(self, edit):

        def update_ordered_list(lines):
            new_lines = []
            next_num = None
            kind = lambda a: a
            for line in lines:
                match = slu.ORDER_LIST_PATTERN.match(line)
                if not match:
                    new_lines.append(line)
                    continue
                new_line = match.group(1) + \
                              (kind(next_num) or match.group(2)) + \
                              match.group(3) + match.group(4)
                new_lines.append(new_line)

                if not next_num:
                    try:
                        next_num = int(match.group(2))
                        kind = str
                    except ValueError:
                        next_num = ord(match.group(2))
                        kind = chr
                next_num += 1
            return new_lines

        def update_roman_list(lines):
            new_lines = []
            next_num = None
            kind = lambda a: a
            for line in lines:
                match = slu.ROMAN_PATTERN.match(line)
                if not match:
                    new_lines.append(line)
                    continue
                new_line = match.group(1) + \
                              (kind(next_num) or match.group(2)) + \
                              match.group(3) + match.group(4)
                new_lines.append(new_line)

                if not next_num:
                    actual = match.group(2)
                    next_num = from_roman(actual.upper())

                    if actual == actual.lower():
                        kind = lambda a: to_roman(a).lower()
                    else:
                        kind = to_roman
                next_num += 1
            return new_lines



        for region in self.view.sel():
            line_region = self.view.line(region)
            # the content before point at the current line.
            before_point_region = sublime.Region(line_region.a,
                                                 region.a)
            before_point_content = self.view.substr(before_point_region)
            # Disable smart list when folded.
            folded = False
            for i in self.view.folded_regions():
                if i.contains(before_point_region):
                    self.view.insert(edit, region.a, '\n')
                    folded = True
            if folded:
                break

            match = slu.EMPTY_LIST_PATTERN.match(before_point_content)
            if match:
                insert_text = match.group(1) + \
                              re.sub(r'\S', ' ', str(match.group(2))) + \
                              match.group(3)
                self.view.erase(edit, before_point_region)
                self.view.insert(edit, line_region.a, insert_text)
                break

            match = slu.ROMAN_PATTERN.match(before_point_content)
            if match:
                actual = match.group(2)
                next_num = to_roman(from_roman(actual.upper()) + 1)
                if actual == actual.lower():
                    next_num = next_num.lower()

                insert_text = match.group(1) + \
                              next_num + \
                              match.group(3)
                self.view.insert(edit, region.a, "\n" + insert_text)

                # backup the cursor position
                pos = self.view.sel()[0].a

                # update the whole list
                region, lines, indent = self.get_block_bounds()
                new_list = update_roman_list(lines)
                self.view.replace(edit, region, '\n'.join(new_list) + '\n')
                # restore the cursor position
                self.view.sel().clear()
                self.view.sel().add(sublime.Region(pos, pos))
                self.view.show(pos)

                break


            match = slu.ORDER_LIST_PATTERN.match(before_point_content)
            if match:
                try:
                    next_num = str(int(match.group(2)) + 1)
                except ValueError:
                    next_num = chr(ord(match.group(2)) + 1)

                insert_text = match.group(1) + \
                              next_num + \
                              match.group(3)
                self.view.insert(edit, region.a, "\n" + insert_text)

                # backup the cursor position
                pos = self.view.sel()[0].a

                # update the whole list
                region, lines, indent = self.get_block_bounds()
                new_list = update_ordered_list(lines)
                self.view.replace(edit, region, '\n'.join(new_list) + '\n')
                # restore the cursor position
                self.view.sel().clear()
                self.view.sel().add(sublime.Region(pos, pos))
                self.view.show(pos)
                break

            match = slu.UNORDER_LIST_PATTERN.match(before_point_content)
            if match:
                insert_text = match.group(1) + match.group(2)
                self.view.insert(edit, region.a, "\n" + insert_text)
                break

            match = slu.NONLIST_PATTERN.match(before_point_content)
            if match:
                insert_text = match.group(1) + match.group(2)
                self.view.insert(edit, region.a, "\n" + insert_text)
                break

            self.view.insert(edit, region.a, '\n' + \
                             re.sub(r'\S+\s*', '', before_point_content))
        self.adjust_view()

    def adjust_view(self):
        for region in self.view.sel():
            self.view.show(region)

#smartlistsENDsmartlistsENDsmartlistsENDsmartlistsENDsmartlistsENDsmartlistsENDsmartlistsEND

#indentlistsSTARTindentlistsSTARTindentlistsSTARTindentlistsSTARTindentlistsSTARTindentlistsSTART

class IndentListItemCommand(sublime_plugin.TextCommand):
    bullet_pattern = r'([-+*]|([(]?(\d+|#|[a-y]|[A-Y]|[MDCLXVImdclxvi]+))([).]))'
    bullet_pattern_re = re.compile(bullet_pattern)
    line_pattern_re = re.compile(r'^\s*' + bullet_pattern)
    spaces_re = re.compile(r'^\s*')

    def run(self, edit, reverse=False):
        for region in self.view.sel():
            if region.a != region.b:
                continue

            line = self.view.line(region)
            line_content = self.view.substr(line)

            new_line = line_content

            m = self.line_pattern_re.match(new_line)
            if not m:
                return

            # Determine how to indent (tab or spaces)
            tab_str = self.view.settings().get('tab_size', 4) * ' '
            sep_str = ' ' if m.group(4) else ''

            prev_line = self.view.line(sublime.Region(line.begin() - 1, line.begin() - 1))
            prev_line_content = self.view.substr(prev_line)

            prev_prev_line = self.view.line(sublime.Region(prev_line.begin() - 1, prev_line.begin() - 1))
            prev_prev_line_content = self.view.substr(prev_prev_line)

            if not reverse:
                # Do the indentation
                new_line = self.bullet_pattern_re.sub(tab_str + sep_str + r'\1', new_line)

                # Insert the new item
                if prev_line_content:
                    new_line = '\n' + new_line

            else:
                if not new_line.startswith(tab_str):
                    continue
                # Do the unindentation
                new_line = re.sub(tab_str + sep_str + self.bullet_pattern, r'\1', new_line)

                # Insert the new item
                if prev_line_content:
                    new_line = '\n' + new_line
                else:
                    prev_spaces = self.spaces_re.match(prev_prev_line_content).group(0)
                    spaces = self.spaces_re.match(new_line).group(0)
                    if prev_spaces == spaces:
                        line = sublime.Region(line.begin() - 1, line.end())

            endings = ['.', ')']

            # Transform the bullet to the next/previous bullet type
            if self.view.settings().get('list_indent_auto_switch_bullet', True):
                bullets = self.view.settings().get('list_indent_bullets', ['*', '-', '+'])

                def change_bullet(m):
                    bullet = m.group(1)
                    try:
                        return bullets[(bullets.index(bullet) + (1 if not reverse else -1)) % len(bullets)]
                    except ValueError:
                        pass
                    n = m.group(2)
                    ending = endings[(endings.index(m.group(4)) + (1 if not reverse else -1)) % len(endings)]
                    if n.isdigit():
                        return '${1:a}' + ending
                    elif n != '#':
                        return '${1:0}' + ending
                    return m.group(2) + ending
                new_line = self.bullet_pattern_re.sub(change_bullet, new_line)

            self.view.replace(edit, line, '')
            self.view.run_command('insert_snippet', {'contents': new_line})

    def is_enabled(self):
        return bool(self.view.score_selector(self.view.sel()[0].a, 'text.restructuredtext'))

#indentlistsENDindentlistsENDindentlistsENDindentlistsENDindentlistsENDindentlistsEND

#simpletableSTARTsimpletableSTARTsimpletableSTARTsimpletableSTARTsimpletableSTARTsimpletableSTART

class SimpletableCommand(BaseBlockCommand):

    _SEPARATOR = '  '

    def get_result(self, indent, table):
        result = '\n'.join(self._draw_table(indent, table))
        result += '\n'
        return result

    def run(self, edit):
        region, lines, indent = self.get_block_bounds()
        table = self._parse_table(lines)
        result = self.get_result(indent, table)
        self.view.replace(edit, region, result)

    def _split_table_cells(self, row_string):
        return re.split(r'\s\s+', row_string.strip())

    def _parse_table(self, raw_lines):
        parsed_lines = []
        for row_string in raw_lines:
            if not self._row_is_separator(row_string):
                parsed_lines.append(self._split_table_cells(row_string))
        return parsed_lines

    def _row_is_separator(self, row):
        return re.match('^[\t =]+$', row)

    def _table_header_line(self, widths):
        linechar = '='
        parts = []
        for width in widths:
            parts.append(linechar * width)
        return SimpletableCommand._SEPARATOR.join(parts)

    def _get_column_max_widths(self, table):
        widths = []
        for row in table:
            num_fields = len(row)
            # dynamically grow
            if num_fields >= len(widths):
                widths.extend([0] * (num_fields - len(widths)))
            for i in range(num_fields):
                field_width = len(row[i])
                widths[i] = max(widths[i], field_width)
        return widths

    def _pad_fields(self, row, width_formats):
        """ Pad all fields using width formats """
        new_row = []
        for i in range(len(row)):
            col = row[i]
            col = width_formats[i] % col
            new_row.append(col)
        return new_row

    def _draw_table(self, indent, table):
        if not table:
            return []
        col_widths = self._get_column_max_widths(table)
        # Reserve room for separater
        len_sep = len(SimpletableCommand._SEPARATOR)
        sep_col_widths = [(col + len_sep) for col in col_widths]
        width_formats = [('%-' + str(w) + 's' + SimpletableCommand._SEPARATOR) for w in col_widths]

        header_line = self._table_header_line(sep_col_widths)
        output = [indent + header_line]
        first = True
        for row in table:
            # draw the lines (num_lines) for this row
            row = self._pad_fields(row, width_formats)
            output.append(indent + SimpletableCommand._SEPARATOR.join(row))
            # draw the under separator for header
            if first:
                output.append(indent + header_line)
                first = False

        output.append(indent + header_line)
        return output

#simpletableENDsimpletableENDsimpletableENDsimpletableENDsimpletableENDsimpletableEND

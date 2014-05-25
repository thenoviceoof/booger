# The MIT License (MIT)
#
# Copyright (c) <2012-2014> <thenoviceoof>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
################################################################################

import curses
import locale

# hack to get curses+unicode working
locale.setlocale(locale.LC_ALL, '')

################################################################################
# constants

ELLIPSE = u'\u2026'

# attributes
# why not bits? better tooling around strings
ATTRIBUTES = {
    'B': curses.A_BOLD,
    'S': curses.A_STANDOUT,
    'U': curses.A_UNDERLINE,
    'R': curses.A_REVERSE,  # reverse the colors
}

class Exit(Exception):
    pass

################################################################################
# utilities

def log(stuff):
    f = open('log', 'a')
    print >>f, stuff

################################################################################
# class hierarchy

class Application(object):
    current_window = None
    windows = {}

    screen = None
    window = None

    colors = [('black', 'white')]

    def run(self):
        curses.wrapper(self.run_curses)

    def run_curses(self, screen):
        # init some curses geometry
        self.screen = screen

        # set up curses colors
        curses.use_default_colors()
        curses.curs_set(0)
        assert len(self.colors) <= 4, 'Too many colors defined'
        assert len(self.colors) > 0, 'Not enough colors defined'
        for i,c in enumerate(self.colors):
            background = getattr(curses, 'COLOR_' + c[0].upper())
            foreground = getattr(curses, 'COLOR_' + c[1].upper())
            curses.init_pair(i, background, foreground)

        # wait for a character for only 0.1s
        curses.halfdelay(1)

        # use the first window as the default window
        self.current_window = self.windows['default']
        self.render()

        while 1:
            input_value = screen.getch()
            # handle non-character input
            try:
                key = chr(input_value)
            except ValueError:
                key = input_value
            # pass the character input to the event loop
            try:
                self.handle(key)
            except Exit:
                return

    def get_size(self):
        return self.screen.getmaxyx()[1], self.screen.getmaxyx()[0]

    def render(self):
        self.screen.clear()
        size = self.get_size()
        w,h = size
        rlines, rstyles = self.current_window.render(size)
        for i,res in enumerate(zip(rlines, rstyles)):
            line, styles = res
            # convert to a unified representation
            style_chars = ['' for j in range(w)]
            for style, start, end in styles:
                for j in range(start, end):
                    style_chars[j] += style
            # convert back to ranges
            style_ranges = []
            current = None
            current_start = None
            for j,s in enumerate(style_chars):
                if s != current:
                    if current_start is not None:
                        style_ranges.append((current, current_start, j))
                    current_start = j
                    current = s
            style_ranges.append((current, current_start, j+1))
            # output the strings with the right styles
            for style, start, end in style_ranges:
                style_attr = 0
                for char in style:
                    style_attr |= ATTRIBUTES.get(char)
                # catch scrolling-past the end of the screen error
                try:
                    self.screen.addstr(i, start,
                                       line[start:end].encode('utf8'),
                                       style_attr)
                except curses.error as e:
                    if i < h - 1 and end == w:
                        raise e
        self.screen.refresh()

    def _switch_window(self, window_name, args=None):
        window = self.windows[window_name]
        self.current_window = window
        if args is not None:
            for k,v in args.iteritems():
                setattr(window, k, v)

    def handle(self, key):
        # see if the application needs to run it's own handler
        signal = self.current_window.handle(key)
        if signal is None:
            # default behavior is to just quit
            if key == 'q':
                if self.current_window is not self.windows['default']:
                    self._switch_window('default')
                    self.render()
                else:
                    raise Exit
            elif key == curses.KEY_RESIZE:
                self.render()
        elif signal == 'redraw':
            self.render()
        elif isinstance(signal, tuple):
            if len(signal) > 0 and signal[0] == 'window':
                _, window_name, window_args = signal
                self._switch_window(window_name, window_args)
                self.render()

################################################################################

class Window(object):
    def handle(self, key):
        return

class Box(Window):
    title_parts = []
    option_parts = []
    spacing = 2
    force = False

    window = None

    def __init__(self, window, title_parts=[], option_parts=[],
                 spacing=2, force=None):
        self.window = window
        self.title_parts = list(title_parts)
        self.option_parts = list(option_parts)
        self.spacing = spacing
        if force is not None:
            self.force = force

    def render(self, size):
        w,h = size
        rlines, rstyles = self.window.render((max(w-2,0),
                                              max(h-2,0) if h else h))
        # make decorative lines
        top_line = self.render_inset(self.title_parts, w-2)
        bot_line = self.render_inset(self.option_parts, w-2, align='right')
        top_line = u'\u250c' + top_line + u'\u2510'
        bot_line = u'\u2514' + bot_line + u'\u2518'
        # wrap content
        if self.force and h is not None and len(rlines) < h - 2:
            rlines += [' ' * (w-2) for i in range(h - 2 - len(rlines))]
            rstyles += [[('', 0, w-2)] for i in range(h - 2 - len(rstyles))]
        lines = [(u'\u2502' + line + u'\u2502') for line in rlines]
        lines = [top_line] + lines + [bot_line]
        # wrap up styles
        styles = [[(s[0], s[1]+1, s[2]+1) for s in line] for line in rstyles]
        styles = [[]] + styles + [[]]
        return lines, styles

    def render_inset(self, parts, width, align='left'):
        spacer = u'\u2500' * self.spacing
        accum = spacer
        for part in parts:
            accum += part
            accum += spacer
        # is it too long?
        if len(accum) > width:
            # can we just chop back the spacers?
            if len(accum.rstrip(u'\u2500')) <= width:
                accum = accum.rstrip(u'\u2500')
            else:
                # just lop it off, add an ellipse at the end (-1 for ellipse)
                accum = accum[:width - 1]
                accum += ELLIPSE
        # fill in extra, if needed
        lines = max(width - len(accum), 0) * u'\u2500'
        if align == 'right':  # assume it's left aligned by default
            accum = lines + accum
        else:
            accum += lines
        return accum

    def handle(self, key):
        return self.window.handle(key)

class VerticalPile(Window):
    windows = []
    current_window = None

    def __init__(self, *args, **kwargs):
        self.windows = args
        if kwargs.get('index'):
            index = kwargs.get('index')
        else:
            index = 0
        self.current_window = args[index]

    def render(self, size):
        w,h = size
        lines = []
        styles = []
        htmp = None
        for win in self.windows:
            if h is not None:
                htmp = h - len(lines)
            wlines, wstyles = win.render((w, htmp))
            lines.extend(wlines)
            styles.extend(wstyles)
            if h is not None and len(lines) > h:
                lines = lines[:h]
                styles = styles[:h]
                break
        return lines, styles

    def handle(self, key):
        # don't do anything interesting with the signal
        signal = self.current_window.handle(key)
        return signal

class VerticalPileEqual(VerticalPile):
    def render(self, size):
        w,h = size
        lines = []
        styles = []
        htmp = None
        for win in self.windows:
            # handle special case, let last window take up orphaned rows
            if win is self.windows[-1]:
                htmp = h - len(lines)
            elif h is not None:
                htmp = h / len(self.windows)
            wlines, wstyles = win.render((w, htmp))
            # pad out lines if necessary
            if len(wlines) < htmp:
                wlines += (htmp - len(wlines)) * [' ' * w]
                wstyles += (htmp - len(wstyles)) * [tuple()]
            lines.extend(wlines)
            styles.extend(wstyles)
            if h is not None and len(lines) > h:
                lines = lines[:h]
                styles = styles[:h]
                break
        return lines, styles

class List(Window):
    windows = []
    current_window = None
    # which window is current
    _index = None
    # how far the windows are, in terms of rows
    scroll = 0

    def __init__(self, *args):
        self.windows = list(args)
        if self._index:
            self.current_window = args[self._index]

    @property
    def index(self):
        return self._index

    # allow inherited classes to override index setting behavior
    def _set_index(self, index):
        # do bounds checking
        if index is None:
            pass
        elif index >= len(self.windows):
            index = len(self.windows) - 1
        elif index < 0:
            index = 0
        self._index = index
        if index is None:
            self.current_window = None
        else:
            self.current_window = self.windows[index]

    @index.setter
    def index(self, index):
        self._set_index(index)

    def add(self, window):
        self.windows.append(window)

    def clear(self):
        self.index = None
        self.windows = []

    def render(self, size):
        w,h = size
        lines, styles, current_row, current_end = self.render_list((w-1,None))
        # just re-render short enough content
        if len(lines) < h:
            lines, styles, current_row, current_end = self.render_list((w,None))
            # double check
            if len(lines) < h:
                return lines, styles
        # draw a persistent scroll bar
        lines = [l + '|' for l in lines]
        current_size = max(int(h * (float(h) / len(lines))), 1)
        # do current bounds checking
        if current_end > self.scroll + h:
            self.scroll = current_end - h
        if current_row < self.scroll:
            self.scroll = current_row
        percentage_scrolled = float(max(self.scroll, 0)) / len(lines)
        # slice the right lines
        lines = lines[self.scroll:self.scroll + h]
        styles = styles[self.scroll:self.scroll + h]
        # place the scroll bar in the right place
        location = int(len(lines) * percentage_scrolled)
        for i in range(location, min(location + current_size, h)):
            # can't assign to tuple index
            lines[i] = lines[i][:-1] + '#'

        return lines, styles

    def render_list(self, size):
        w,h = size
        lines = []
        styles = []
        current_row = 0
        current_end = 0
        for win in self.windows:
            wlines, wstyles = win.render((w,None))
            if win is self.current_window:
                current_row = len(lines)
                current_end = len(lines) + len(wlines)
                wstyles = [s + [('R', 0, w)] for s in wstyles]
            lines.extend(wlines)
            styles.extend(wstyles)
        return lines, styles, current_row, current_end

    def handle(self, key):
        if self.current_window is not None:
            signal = self.current_window.handle(key)
        else:
            signal = None
        if signal is None:
            if key in ('n', curses.KEY_UP, 'p', curses.KEY_DOWN):
                if self.index is None:
                    self.index = 0
                elif key in ('n', curses.KEY_DOWN):
                    self.index += 1
                elif key in ('p', curses.KEY_UP):
                    self.index -= 1
                return 'redraw'
        return signal

class Scrollable(Window):
    window = None
    # how far the window is, in terms of rows
    scroll = 0
    prev_h = 0

    def __init__(self, window, scroll=0):
        self.window = window
        self.scroll = scroll

    def render(self, size):
        w,h = size
        # store h for scrolling
        if h is not None:
            self.prev_h = h
        lines, styles = self.window.render((w-1,None))
        # just re-render short enough content
        if len(lines) < h:
            lines, styles = self.window.render((w,None))
            # double check
            if len(lines) < h:
                return lines, styles
        # fix up scroll
        if self.scroll < 0:
            self.scroll = 0
        if self.scroll + h > len(lines):
            self.scroll = len(lines) - h
        # draw a persistent scroll bar
        lines = [l + '|' for l in lines]
        current_size = max(int(h * (float(h) / len(lines))), 1)
        percentage_scrolled = float(max(self.scroll, 0)) / len(lines)
        # slice the right lines
        lines = lines[self.scroll:self.scroll + h]
        styles = styles[self.scroll:self.scroll + h]
        # place the scroll bar in the right place
        location = int(len(lines) * percentage_scrolled)
        for i in range(location, min(location + current_size, h)):
            # can't assign to tuple index
            lines[i] = lines[i][:-1] + '#'

        return lines, styles

    def handle(self, key):
        if self.window is not None:
            signal = self.window.handle(key)
        else:
            signal = None
        if signal is None:
            if key in ('n', curses.KEY_UP, 'p', curses.KEY_DOWN,
                       curses.KEY_PPAGE, curses.KEY_NPAGE):
                if key in ('n', curses.KEY_DOWN):
                    self.scroll += 1
                elif key in ('p', curses.KEY_UP):
                    self.scroll -= 1
                elif key == curses.KEY_NPAGE:
                    self.scroll += self.prev_h
                elif key == curses.KEY_PPAGE:
                    self.scroll -= self.prev_h
                return 'redraw'
        return signal

################################################################################

class Text(Window):
    text = ''
    style = ''
    indent = ''
    tab = '    '

    def __init__(self, text, style='', indent='', tab=None):
        self.text = text
        self.style = style
        self.indent = indent
        if tab is not None:
            self.tab = tab

    def render(self, size):
        text = self.text
        text = text.replace('\t', self.tab)
        texts = text.split('\n')
        w,h = size
        lines = []
        newline = True
        while texts and (len(lines) < h if h else True):
            if newline:
                lines.append(texts[0][:w])
            else:
                lines.append(self.indent + texts[0][:w - len(self.indent)])
            texts[0] = texts[0][w:]
            newline = False
            if not texts[0]:
                newline = True
                texts.pop(0)
        # pad everything out
        lines = [line + ' ' * (w - len(line)) for line in lines]
        # pad out styles
        styles = [[(self.style, 0, w)] for i in range(len(lines))]
        return lines, styles

class TextNoWrap(Window):
    text = ''
    style = ''
    tab = '    '

    def __init__(self, text, style='', tab=None):
        self.text = text
        self.style = style
        if tab is not None:
            self.tab = tab

    def render(self, size):
        text = self.text
        text = text.replace('\t', self.tab)
        texts = text.split('\n')
        w,h = size
        lines = []
        while texts and (len(lines) < h if h else True):
            if len(texts[0]) > w:
                lines.append(texts[0][:w-1] + ELLIPSE)
            else:
                lines.append(texts[0])
            texts.pop(0)
        # pad everything out
        lines = [line + ' ' * (w - len(line)) for line in lines]
        # pad out styles
        styles = [[(self.style, 0, w)] for i in range(len(lines))]
        return lines, styles

class TextLineNumbers(Window):
    _text = ''
    texts = []
    style = ''
    tab = '    '

    def __init__(self, text, style='', tab=None):
        self.text = text
        self.style = style
        if tab is not None:
            self.tab = tab

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        text = text.replace('\t', self.tab)
        self.texts = text.split('\n')

    def render(self, size):
        w,h = size
        total = len(self.texts)
        nlen = len('%d' % total)
        inner_width = w - nlen - 1  # +1 for divider
        lines = []
        i = 0
        j = 0
        while i < len(self.texts) and (len(lines) < h if h else True):
            if j == 0:
                number = ('%d' % i).rjust(nlen)
                lines.append(number + '|' + self.texts[i][j:j + inner_width])
            else:
                lines.append((' ' * nlen) + '|' + self.texts[i][j:j + inner_width])
            j += inner_width
            if j >= len(self.texts[i]):
                i += 1
                j = 0
        # pad everything out
        lines = [line + ' ' * (w - len(line)) for line in lines]
        # pad out styles
        styles = [[(self.style, 0, w)] for i in range(len(lines))]
        return lines, styles

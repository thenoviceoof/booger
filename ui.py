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
    modals = {}

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

    def handle(self, key):
        # see if the application needs to run it's own handler
        signal = self.current_window.handle(key)
        if signal is None:
            # default behavior is to just quit
            if key == 'q':
                raise Exit
        elif signal == 'redraw':
            self.render()

################################################################################

class Window(object):
    def handle(self, key):
        return

class Box(Window):
    title_parts = []
    option_parts = []
    spacing = 2

    window = None

    def __init__(self, window, title_parts=[], option_parts=[], spacing=2):
        self.window = window
        self.title_parts = title_parts
        self.option_parts = option_parts
        self.spacing = spacing

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

class VerticalPile(Window):
    windows = []
    current_window = None

    def __init__(self, *args):
        self.windows = args
        self.current_window = args[0]

    def render(self, size):
        w,h = size
        lines = []
        styles = []
        for win in self.windows:
            wlines, wstyles = win.render((w,h-len(lines)))
            lines.extend(wlines)
            styles.extend(wstyles)
            if len(lines) > h:
                lines = lines[:h]
                styles = styles[:h]
                break
        return lines, styles

    def handle(self, key):
        # don't do anything interesting with the signal
        signal = self.current_window.handle(key)
        return signal

class HorizontalPile(Window):
    pass

class List(Window):
    windows = []
    current_window = None
    # which window is current
    _index = 0
    # how far the windows are, in terms of rows
    scroll = 0

    def __init__(self, *args):
        self.windows = args
        self.current_window = args[self._index]

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        # do bounds checking
        if index >= len(self.windows):
            index = len(self.windows) - 1
        if index < 0:
            index = 0
        self._index = index
        self.current_window = self.windows[index]

    def render(self, size):
        w,h = size
        lines, styles, current_row, current_end = self.render_list((w-1,h))
        # just re-render short enough content
        if len(lines) < h:
            lines, styles, current_row, current_end = self.render_list((w,h))
            # double check
            if len(lines) < h:
                return lines, styles
        # draw a persistent scroll bar
        lines = [l + '|' for l in lines]
        percentage_scrolled = float(current_row) / len(lines)
        current_size = max(int(h * (float(current_end - current_row) /
                                    len(lines))),
                           1)
        # do current bounds checking
        if current_end > self.scroll + h:
            self.scroll = current_end - h
        if current_row < self.scroll:
            self.scroll = current_row
        # slice the right lines
        lines = lines[self.scroll:self.scroll + h]
        styles = styles[self.scroll:self.scroll + h]
        # place the scroll bar in the right place
        location = int(len(lines) * percentage_scrolled)
        for i in range(current_size):
            lines[location + i] = lines[location + i][:-1] + '#'

        return lines, styles

    def render_list(self, size):
        w,h = size
        lines = []
        styles = []
        current_row = 0
        current_end = 0
        for win in self.windows:
            wlines, wstyles = win.render((w,h-len(lines)))
            if win is self.current_window:
                current_row = len(lines)
                current_end = len(lines) + len(wlines)
                wstyles = [s + [('R', 0, w)] for s in wstyles]
            lines.extend(wlines)
            styles.extend(wstyles)
        return lines, styles, current_row, current_end

    def handle(self, key):
        signal = self.current_window.handle(key)
        if signal is None:
            if key in ('n', curses.KEY_DOWN):
                self.index += 1
            if key in ('p', curses.KEY_UP):
                self.index -= 1
            if key in ('n', curses.KEY_UP, 'p', curses.KEY_DOWN):
                return 'redraw'

################################################################################

class Text(Window):
    text = ''
    style = ''

    def __init__(self, text, style=''):
        self.text = text
        self.style = style

    def render(self, size):
        text = self.text
        texts = text.split('\n')
        w,h = size
        lines = []
        while texts and (len(lines) < h if h else True):
            lines.append(texts[0][:w])
            texts[0] = texts[0][w:]
            if not texts[0]:
                texts.pop(0)
        # pad everything out
        lines = [line + ' ' * (w - len(line)) for line in lines]
        # pad out styles
        styles = [[(self.style, 0, w)] for i in range(len(lines))]
        return lines, styles

class TextNoWrap(Window):
    text = ''
    style = ''

    def __init__(self, text, style=''):
        self.text = text
        self.style = style

    def render(self, size):
        text = self.text
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

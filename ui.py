import curses
import locale

locale.setlocale(locale.LC_ALL, '')

################################################################################
# utilities

ELLIPSE = u'\u2026'

class Exit(Exception):
    pass

################################################################################
# class hierarchy

class Application(object):
    current_window = None
    windows = {}
    modals = {}

    screen = None
    window = None

    def run(self):
        curses.wrapper(self.run_curses)

    def run_curses(self, screen):
        # init some curses geometry
        self.screen = screen

        # set up curses colors
        curses.use_default_colors()
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
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
                continue
            # pass the character input to the event loop
            try:
                self.handle(key)
            except Exit:
                return

    def get_size(self):
        return self.screen.getmaxyx()[1], self.screen.getmaxyx()[0]

    def render(self):
        size = self.get_size()
        results = self.current_window.render(size)
        for i,line in enumerate(results):
            self.screen.addstr(i,0, line.encode('utf8'))

    def handle(self, key):
        if key == 'q':
            raise Exit

################################################################################

class Window(object):
    def render(self):
        pass

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
        results = self.window.render((max(w-2,0), max(h-2,0) if h else h))
        # make decorative lines
        top_line = self.render_inset(self.title_parts, w-2)
        bot_line = self.render_inset(self.option_parts, w-2, align='right')
        top_line = u'\u250c' + top_line + u'\u2510'
        bot_line = u'\u2514' + bot_line + u'\u2518'
        # wrap content
        lines = [(u'\u2502' + line + u'\u2502') for line in results]
        lines = [top_line] + lines + [bot_line]
        return lines

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
    def render(self, size):
        pass

class HorizontalPile(Window):
    pass

class List(Window):
    pass

################################################################################

class StatusBar(Window):
    parts = []

    def __init__(self, parts):
        self.parts = parts

    def render(self, size):
        pass

class Text(Window):
    text = ''

    def __init__(self, text):
        self.text = text

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
        return lines

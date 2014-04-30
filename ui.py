import curses

################################################################################
# utilities

def format_box_inset(format_str, line_length, align='left'):
    '''
    Utility for creating LineBox-like titles, sans the corners
    '''
    prev_part_str = False
    accum = u''
    for part in format_str:
        # insert on int
        if isinstance(part, int):
            part = u'\u2500' * part
            prev_part_str = False
        elif prev_part_str:
            # two strings in a row? insert a separator
            part = u'\u2500' + part
            prev_part_str = True
        else:
            prev_part_str = True
        accum += part
    # is it too long?
    if len(accum) > line_length:
        # can we chop off enough line segments?
        if len(accum.rstrip(u'\u2500')) <= line_length:
            accum = accum.rstrip(u'\u2500')
        else:
            # just lop it off, add an ellipse at the end (-1 for ellipse)
            accum = accum[:line_length - 1]
            accum += ELLIPSE
    # fill in extra lines, if needed (max)
    lines = max(line_length - len(accum), 0) * u'\u2500'
    if align == 'right':  # assume it's left aligned by default
        accum = lines + accum
    else:
        accum += lines
    return accum

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
        for line in results:
            self.screen.addstr(0,0, line)

    def handle(self, key):
        if key == 'q':
            raise Exit

################################################################################

class Window(object):
    def render(self):
        pass

class Modal(Window):
    pass

class VerticalPile(Window):
    def render():
        pass

class HorizontalPile(Window):
    pass

class List(Window):
    pass

################################################################################

class TextBox(Window):
    text = ''

    def __init__(self, text):
        self.text = text

    def render(self, size=None):
        text = self.text
        if len(size) > 1:
            w,h = size
        else:
            w,h = size[0], None
        lines = []
        while text and (len(lines) < h if h else True):
            lines.append(text[:w])
            text = text[w:]
        return lines

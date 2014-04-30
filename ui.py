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

################################################################################
# class hierarchy

class Application(object):
    windows = []
    modals = []

    def run(self):
        curses.wrapper(self.run_curses)

    def run_curses(self):
        pass

class Window(object):
    def render(self):
        pass

class Modal(Window):
    pass

class VerticalPile(Window):
    pass

class HorizontalPile(Window):
    pass

class List(Window):
    pass

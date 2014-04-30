import curses

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

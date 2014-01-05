'''
This is a library for building textual-GUIs, based on top of ncurses
'''

import curses
import curses.textpad

MAX_PAD_WIDTH = 300
MAX_PAD_HEIGHT = 2000

################################################################################
# what it SHOULD look like

'''
class TestItem(Window):
    child = TestItemTraceback

    def __init__(self):
        
        super().__init__()

    def chrome(self):
        'draw some chrome'
        add_str

class TestList(Grid):
    direction = 'vertical'
    children = [] # display an empty list

class Statusbar(TextWindow):
    style = ngui.highlight
    def draw(self):
        self.contents = "generate some text"
        super().draw()

class Main(Grid):
    direction = 'vertical'
    # Statusbar has size (1, None), and TestList has size (None, None)
    # so it takes up everything
    children = [Statusbar, TestList]
    # maybe this should be a named tuple, then we can do:
    relative_sizes = {
        'status': 0.3,
        'test': 0.7,
        }

class GUI(MainWindow):
    child = Main
    modals = {'': TracebackModal,
              'search': SearchModal}

    def loop(self):
        # handle test queue here, add tests here
        super().loop()
'''

################################################################################

class TextWindow(object):
    '''
    Display some text. Wrap it, scroll it
    '''
    def __init__(self, screen=None, size=None, *args, **kwargs):
        '''
        Expects a screen, possibly a size
        '''
        self.screen = screen
        self.window = curses.newpad()
        self.size = size
        self.contents = ''

        self.selected = False
        self.dirty = True

    def draw(self):
        '''
        Draw the contents 
        '''
        if not self.dirty:
            return
        if self.selected:
            return

class Grid(object):
    '''
    This gathers a bunch of windows and draws them in a grid fashion
    Either percentage based or line based, not both
    Maybe just a window list, I don't need a grid, and 2d is hairy
    '''

class WindowChrome(object):
    '''
    A container for content, which displays chrome around that content
    '''

class MainWindow(object):
    '''
    The root element, contains the event loop
    '''

    def run(self):
        '''
        Starts executing the loop, taking advantage of python's curses wrapper
        '''
        curses.wrapper(self.start)

    def start(self, screen):
        '''
        The method executed by the curses wrapper in run, should not
        be overridden
        '''
        self.setup(screen)

        try:
            while 1:
                loopp = self.loop(screen)
                if loopp:
                    break
        except KeyboardInterrupt:
            pass

        self.cleanup(screen)

    def loop(self, screen):
        '''
        Override this method to define the behavior on each loop,
        which by default only mutates the with input and draws the
        .child, if it exists

        Returning a truth-y value from this method will exit the loop
        '''
        char = screen.getch()
        self.input(char)
        self.draw(screen)

    def input(self, char):
        if hasattr(self, 'child_window'):
            self.child_window.input(char)
    def draw(self, screen):
        if hasattr(self, 'child_window'):
            self.child_window.draw()

    def setup(self, screen):
        '''
        Override this method to execute curses-related things before
        entering the event loop
        '''
        # set up curses colors
        curses.use_default_colors()
        # wait for a character for 0.1s
        curses.halfdelay(1)
        self.child = TextWindow()
        # instantiate the child
        if hasattr(self, 'child'):
            self.child_window = self.child()

    def cleanup(self, screen):
        '''
        Override this method to execute curses-related things after
        exiting the event loop
        '''
        pass

w = MainWindow()
w.run()

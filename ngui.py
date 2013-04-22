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
    def __init__(self)

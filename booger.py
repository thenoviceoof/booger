#!/usr/bin/python
################################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# <thenoviceoof> wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day,
# and you think this stuff is worth it, you can buy me a beer in
# return
# Nathan Hwang <thenoviceoof>
################################################################################

import re
import sys
import nose
import Queue
import curses
import threading
import exceptions
from StringIO import StringIO

from nose.plugins import Plugin

################################################################################
# windowing stuff

MAX_PAD_WIDTH = 300
MAX_PAD_HEIGHT = 2000

STATUS_BAR_RUNNING  = 'Tests Running...'
STATUS_BAR_FINISHED = 'Tests Done!     '

TEST_WIN_HEIGHT = 5

def get_new_tests(queue):
    '''
    Retrieves tests from the queue, puts them in the right place
    Returns a tuple:
        list of tuples (status, test object, err)
        whether tests are done
    '''
    try:
        s, t, e = queue.get(block=False)
    except Queue.Empty:
        return [], False
    # tests done
    if s is None and t is None and e is None:
        return [], True
    # keep getting until we're empty
    tests = []
    while 1:
        tests.append((s,t,e))
        try:
            s, t, e = queue.get(block=False)
        except Queue.Empty:
            return tests, False
        # tests done
        if s is None and t is None and e is None:
            return tests, True


class StatusBar(object):
    def __init__(self, screen, *args, **kwargs):
        self.screen = screen
        self.test_counts = {
            'ok': 0,
            'fail': 0,
            'error': 0,
        }
        self.finished = False

        # make the curses object
        size = self.screen.getmaxyx()[1], self.screen.getmaxyx()[0]
        self.window = curses.newwin(1, size[0])
        self.window.attrset(curses.A_BOLD)
        self.window.bkgdset(ord(' '), curses.color_pair(1))
        self.update()

        super(StatusBar, self).__init__(*args, **kwargs)

    def update(self):
        self.window.clear()
        status = []
        if self.finished:
            status += [STATUS_BAR_FINISHED]
        else:
            status += [STATUS_BAR_RUNNING]
        status += ['{0}: {1}'.format(x, self.test_counts[x])
                   for x in ['ok', 'error', 'fail']]
        status_str = ' | '.join(status)
        self.window.addstr(0,0, status_str)
        size = self.screen.getmaxyx()[1], self.screen.getmaxyx()[0]
        self.window.refresh()

    def add_test(self, test_type):
        self.test_counts[test_type] += 1
    def finish(self):
        self.finished = True


def get_frames(tb_ptr):
    # get tb_frames
    frames = []
    while tb_ptr:
        frames.append(tb_ptr.tb_frame)
        tb_ptr = tb_ptr.tb_next
    return frames

class TestWindow(object):
    def __init__(self, screen, test_list, test_status, test, err,
                 *args, **kwargs):
        self.screen = screen
        self.window = test_list.subwin(1,1, 0,0)

        self.selected = False
        self.test_status = test_status
        self.test = test
        self.err = err
        self.y = 0

        self.frames = get_frames(self.err[2])

        super(TestWindow, self).__init__(*args, **kwargs)

    def update(self, y=None):
        '''
        We don't actually call refresh, since we expect the TestList
        to be a pad that needs to call refresh itself
        '''
        # store the 
        if y is None:
            y = self.y
        else:
            self.y = y
        traceback_lines = {True: 5, False: 1}[self.selected]
        if traceback_lines > len(self.frames):
            traceback_lines = len(self.frames)
        lines = 3 + traceback_lines * 2

        size = self.screen.getmaxyx()[1], self.screen.getmaxyx()[0]
        self.window.mvderwin(y, 0)
        self.window.resize(lines, size[0])

        self.window.clear()
        self.window.box()

        self.window.addstr(0, 2, ' %s ' % self.test_status[0].upper(), curses.A_BOLD)
        self.window.addstr(0, 7, str(self.test), curses.A_BOLD)

        # display error (type, exception, traceback)
        for i in range(traceback_lines):
            j = -traceback_lines+i
            # get file failed in
            filename = self.frames[j].f_code.co_filename
            self.window.addstr(1 + i*2, 1, filename[:size[0]-2])
            # get line of source code failed on
            f = open(filename)
            line = f.readlines()[self.frames[j].f_lineno-1]
            f.close()
            self.window.addstr(2 + i*2, 1, line.rstrip()[:size[0]])
        # display what and how
        exception_name = self.err[1].__class__.__name__
        err_str = '{0}: {1}'.format(exception_name,
                                    self.err[1].message)[:size[0]-2]
        self.window.addstr(lines-2, 1, err_str)

        # add controls
        if self.selected:
            self.window.addstr(lines-1, size[0]-40, 'Traceback')
            self.window.addstr(lines-1, size[0]-30, 'Stdout')
            self.window.addstr(lines-1, size[0]-20, 'Stderr')
            self.window.addstr(lines-1, size[0]-10, 'Logging')

        return lines

    def select(self):
        self.selected = True
        self.window.bkgdset(ord(' '), curses.color_pair(1))
        self.update()
    def deselect(self):
        self.selected = False
        self.window.bkgdset(ord(' '), curses.color_pair(0))
        self.update()

    def modal(self, modal):
        '''
        Given the modal window, write details to it
        '''
        modal.addstr(0,0, 'Hello world')

class TestModal(object):
    def __init__(self, screen, *args, **kwargs):
        self.screen = screen
        self.window = curses.newpad(MAX_PAD_HEIGHT, MAX_PAD_WIDTH)

        self.test = None
        self.err = None

        self.opened = False

    def update(self):
        if not self.opened:
            return

        self.frames = get_frames(self.err[2])

        size = self.screen.getmaxyx()[1], self.screen.getmaxyx()[0]

        self.window.clear()

        # display traceback
        context = 3
        for i in range(len(self.frames)):
            # get file failed in
            filename = self.frames[i].f_code.co_filename
            self.window.bkgdset(ord(' '), curses.color_pair(1))
            self.window.addstr(1 + i*(2+context*2), 1, filename[:size[0]-2])
            self.window.bkgdset(ord(' '), curses.color_pair(0))
            # get line of source code failed on
            f = open(filename)
            lines = f.readlines()
            ln_from, ln_to = (self.frames[i].f_lineno-1 - context,
                              self.frames[i].f_lineno-1 + context)
            ls = lines[ln_from:ln_to]
            if ln_from < 0:
                ls += [''] * (-ln_from)
            if ln_to > len(lines):
                ls += [''] * (len(lines) - ln_to)
            f.close()
            # display lines + context
            for j in range(len(ls)):
                l = ls[j]
                self.window.addstr(2 + i*(2+context*2) + j, 1,
                                   l.rstrip()[:size[0]])
            self.window.addstr(2 + i*(2+context*2) + context, 0, '*')

        if self.test.stdout:
            # self.window.addstr(30, 0, self.test.capturedOutput)
            self.window.addstr(0, 0, self.test.stdout)

        self.window.refresh(0,0, 0,0, size[1]-1, size[0]-1)
    def open(self, test, err):
        self.test = test
        self.err = err

        self.opened = True
    def close(self, test, err):
        self.opened = False

class TestList(object):
    def __init__(self, screen, *args, **kwargs):
        self.screen = screen

        self.window = curses.newpad(MAX_PAD_HEIGHT, MAX_PAD_WIDTH)
        self.window_list = []
        self.modal = TestModal(screen)

        self.cur_test = None

        super(TestList, self).__init__(*args, **kwargs)

    def update(self):
        self.window.clear()
        # sizing
        size = self.screen.getmaxyx()[1], self.screen.getmaxyx()[0]
        acc = 0
        for w in self.window_list:
            acc += w.update(acc)
        self.window.refresh(0,0, 1,0, size[1]-2, size[0]-1)
    def add_test(self, test_status, test, err):
        tw = TestWindow(self.screen, self.window, test_status, test, err)
        self.window_list.append(tw)

    def move_list(self, n=1):
        if len(self.window_list) == 0:
            return

        if self.cur_test is None:
            cur_test = 0
        else:
            cur_test = self.cur_test

        self.window_list[cur_test].deselect()

        if self.cur_test is None:
            self.cur_test = 0
        else:
            self.cur_test += n
            self.cur_test %= len(self.window_list)

        self.window_list[self.cur_test].select()

    def update_modal(self):
        self.modal.update()
    def open_modal(self):
        if self.cur_test is not None:
            win = self.window_list[self.cur_test]
            self.modal.open(win.test, win.err)
    def close_modal(self):
        pass


# handle book keeping (update areas that need updating)
class TestsGUI(object):
    def __init__(self, screen, *args, **kwargs):
        self.screen = screen
        # state in [list, detail]
        self.state = 'list'

        # state
        self.done = False
        self.new_tests = False

        # gui elements
        self.status_bar = StatusBar(screen)
        self.test_list = TestList(screen)

        super(TestsGUI, self).__init__()

    # draw things
    def update(self):
        self.status_bar.update()
        if self.state == 'list':
            self.test_list.update()
        elif self.state == 'detail':
            self.test_list.update_modal()

    # movement 
    def next(self, n=1):
        if self.state == 'list':
            self.test_list.move_list(n)
    def prev(self, n=1):
        if self.state == 'list':
            self.test_list.move_list(-n)

    # handle modality
    def toggle_modal(self):
        self.screen.clear()
        if self.state == 'list':
            self.state = 'detail'
            self.test_list.open_modal()
        elif self.state == 'detail':
            self.state = 'list'
            self.test_list.close_modal()

    # test related things
    def add_test(self, test_type, test, err):
        # update the status bar
        self.status_bar.add_test(test_type)

        if test_type != 'ok':
            self.test_list.add_test(test_type, test, err)
    def finish(self):
        self.status_bar.finish()

def curses_main(scr, test_queue):
    # set up the main window, which sets up everything else
    interface = TestsGUI(scr)

    # set up curses colors
    curses.use_default_colors()
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    # wait for a character for only 0.1s
    curses.halfdelay(1)

    interface.update()
    tests_done = False
    try:
        while 1:
            # handle input
            c = scr.getch()
            if c == ord('q'):
                return
            elif c in [curses.KEY_DOWN, ord('n')]:
                interface.next()
            elif c in [curses.KEY_UP, ord('p')]:
                interface.prev()
            elif c in [curses.KEY_ENTER, ord('\n')]:
                interface.toggle_modal()
            elif c == curses.KEY_RESIZE:
                interface.update()

            # handle any new tests
            if not tests_done:
                new_tests, tests_done = get_new_tests(test_queue)
            if new_tests:
                for stat, test, err in new_tests:
                    interface.add_test(stat, test, err)
                new_tests = []
            if tests_done:
                interface.finish()

            interface.update()
    except KeyboardInterrupt:
        return

def curses_run(test_queue):
    '''
    Little wrapper to facilitate thread running
    '''
    curses.wrapper(curses_main, test_queue)

################################################################################
# nose plugin

class BoogerPlugin(Plugin):
    '''
    Something
    '''
    enabled = False
    name = 'booger'
    score = 3000

    def __init__(self, *args, **kwargs):
        super(BoogerPlugin, self).__init__(*args, **kwargs)

        self.test_queue = Queue.Queue()
        self.curses = threading.Thread(target=curses_run,
                                       args=(self.test_queue,))
        self.curses.start()

    ############################################################################
    # options
    def options(self, parser, env):
        '''
        Register booger's commandline options
        '''
        parser.add_option(
            '--booger', action = 'store_const',
            default = False, const = True, dest = 'booger',
            help = 'Display captured output in a curses interface')
    def configure(self, options, conf):
        self.conf = conf
        self.enabled = options.booger

    ############################################################################
    # test outcome handler
    def get_stdout(self):
        if isinstance(sys.stdout, StringIO):
            return sys.stdout.getvalue()
        return None

    def addSuccess(self, test):
        self.test_queue.put( ('ok', test, None) )
    def addFailure(self, test, err):
        stdout = self.get_stdout()
        test.stdout = stdout
        self.test_queue.put( ('fail', test, err) )
    def addError(self, test, err):
        stdout = self.get_stdout()
        test.stdout = stdout
        self.test_queue.put( ('error', test, err) )

    ############################################################################
    # handle other boilerplate
    def finalize(self, result):
        while self.stdout:
            self.end_stdcapture()

        self.test_queue.put( (None,None,None) )
        self.curses.join()
    def report(self, stream):
        # stop normal report stdout from printing
        return False
    def setOutputStream(self, stream):
        self.stream = stream
        class Dummy:
            def write(self, *arg):
                pass
            def writeln(self, *arg):
                pass
            def flush(self, *arg):
                pass
        return Dummy()

################################################################################
# main

if __name__ == "__main__":
    nose.main(plugins=[BoogerPlugin()])

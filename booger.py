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
# utils

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

def get_frames(tb_ptr):
    '''
    Gets tb_frames out of the dumb linked list format, into python lists
    '''
    frames = []
    while tb_ptr:
        frames.append(tb_ptr.tb_frame)
        tb_ptr = tb_ptr.tb_next
    return frames

################################################################################
# windowing stuff

MAX_PAD_WIDTH = 300
MAX_PAD_HEIGHT = 2000

STATUS_BAR_RUNNING  = 'Tests Running...'
STATUS_BAR_FINISHED = 'Tests Done!     '

TEST_WIN_HEIGHT = 5

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

        self.window.addstr(0, 2, ' %s ' % self.test_status[0].upper(),
                           curses.A_BOLD)
        self.window.addstr(0, 7, str(self.test)[:size[0]-8], curses.A_BOLD)

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
            self.window.addstr(2 + i*2, 1, line.rstrip()[:size[0]-2])
        # display what and how
        exception = self.test.exception
        exception_name = exception.__class__.__name__
        err_str = '{0}: {1}'.format(exception_name, exception)[:size[0]-2]
        self.window.addstr(lines-2, 1, err_str)

        # add controls
        if self.selected:
            options = ['T_raceback']
            if self.test.capturedOutput:
                options.append('stdO_ut')

            if self.test.capturedLogging:
                options.append('L_ogging')

            acc = 3
            for opt in reversed(options):
                opts = opt.split('_')
                acc += len(opts[0]) + len(opts[1]) + 2
                self.window.addstr(lines-1, size[0]-acc, opts[0][:-1])
                self.window.addstr(lines-1, size[0]-acc + len(opts[0][:-1]),
                                   opts[0][-1], curses.A_BOLD)
                self.window.addstr(lines-1,
                                   size[0]-acc + len(opts[0]),
                                   opts[1])

        return lines

    def select(self):
        self.selected = True
        self.window.bkgdset(ord(' '), curses.color_pair(1))
        self.update()
    def deselect(self):
        self.selected = False
        self.window.bkgdset(ord(' '), curses.color_pair(0))
        self.update()


class TestModal(object):
    def __init__(self, screen, *args, **kwargs):
        self.screen = screen
        self.window = curses.newpad(MAX_PAD_HEIGHT, MAX_PAD_WIDTH)

        self.test = None
        self.err = None

        self.opened = False

    def traceback(self):
        self.type = 'traceback'
        self.update()
        return True
    def output(self):
        if self.test.capturedOutput:
            self.type = 'stdout'
            self.update()
            return True
        else:
            return False
    def logging(self):
        if self.test.capturedLogging:
            self.type = 'logging'
            self.update()
            return True
        else:
            return False
        
    def update_traceback(self):
        size = self.screen.getmaxyx()[1], self.screen.getmaxyx()[0]
        self.frames = get_frames(self.err[2])

        # display traceback
        acc = 1
        context = 5
        for frame in self.frames:
            # get file failed in
            filename = frame.f_code.co_filename
            if re.match(r'(^/usr/lib.*|.*/\.local/lib/.*)', filename):
                context = 0
            else:
                context = 5
            self.window.bkgdset(ord(' '), curses.color_pair(1))
            self.window.addstr(acc, 0, filename[:size[0]-2])
            self.window.bkgdset(ord(' '), curses.color_pair(0))
            # get line of source code failed on
            f = open(filename)
            lines = f.readlines()
            ln_from, ln_to = (frame.f_lineno - 1 - context, frame.f_lineno)
            ls = lines[ln_from:ln_to]
            if ln_from < 0:
                ls = [''] * (-ln_from) + ls
            f.close()
            # display lines + context
            for j in range(len(ls)):
                l = ls[j]
                self.window.addstr(acc + j + 1, 1, l.rstrip()[:size[0]])
            if context:
                self.window.addstr(acc + context + 1, 0, '*')
            acc += 2 + context
    def update_stdout(self):
        self.window.addstr(0, 0, self.test.capturedOutput)
    def update_logging(self):
        self.window.addstr(0, 0, '\n'.join(self.test.capturedLogging))
    def update(self):
        if not self.opened:
            return

        size = self.screen.getmaxyx()[1], self.screen.getmaxyx()[0]
        self.window.clear()

        if self.type == 'traceback':
            self.update_traceback()
        elif self.type == 'stdout':
            self.update_stdout()
        elif self.type == 'logging':
            self.update_logging()

        self.window.refresh(0,0, 0,0, size[1]-1, size[0]-1)
    def open(self, test, err):
        self.test = test
        self.err = err
        self.opened = True
    def close(self):
        self.opened = False

class TestList(object):
    def __init__(self, screen, *args, **kwargs):
        self.screen = screen

        self.window = curses.newpad(MAX_PAD_HEIGHT, MAX_PAD_WIDTH)
        self.window_list = []
        self.modal = TestModal(screen)

        self.cur_test = None
        self.scroll = 0
        self.dirty = True

        super(TestList, self).__init__(*args, **kwargs)

    def update(self):
        if not self.dirty:
            return
        # !! try not clearing the entire list
        self.window.clear()
        # sizing
        size = self.screen.getmaxyx()[1], self.screen.getmaxyx()[0]
        scroll = 0
        acc = 0
        for w in self.window_list:
            if w.selected:
                scroll = acc
            acc += w.update(acc)
        # handle scrolling
        if scroll > self.scroll + size[1] - 10:
            self.scroll = scroll - size[1] + 10
        elif scroll < self.scroll:
            self.scroll = scroll
        # draw the scroll bar
        if acc > size[1]:
            for i in range(size[1]-1):
                self.window.addstr(self.scroll+i,size[0]-1, '|')
            total = acc - (size[1]-1)
            d = int((float(self.scroll) / total) * (size[1] - 2))
            self.window.addstr(self.scroll+d, size[0]-1, '#', curses.A_BOLD)
        # and then do the refresh
        self.window.refresh(self.scroll,0, 1,0, size[1]-1, size[0]-1)
        self.dirty = False
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
        self.dirty = True

    def open_modal(self):
        if self.cur_test is not None:
            win = self.window_list[self.cur_test]
            self.modal.open(win.test, win.err)
        self.dirty = True


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

    # handle input
    def handle_input(self, c):
        if c == ord('q'):
            if self.state == 'list':
                return False
            else:
                self.state = 'list'
                self.modal_close()
                return True
        elif c in [curses.KEY_DOWN, ord('n')]:
            self.next()
        elif c in [curses.KEY_UP, ord('p')]:
            self.prev()
        elif c in [curses.KEY_ENTER, ord('\n')]:
            pass
            # self.toggle_modal()
        elif c in [ord('t'), ord('T')]:
            self.modal_traceback()
        elif c in [ord('o'), ord('O')]:
            self.modal_output()
        elif c in [ord('l'), ord('L')]:
            self.modal_logging()
        elif c == curses.KEY_RESIZE:
            self.update()
        return True

    # draw things
    def update(self):
        self.status_bar.update()
        if self.state == 'list':
            self.test_list.update()
        else:
            self.test_list.modal.update()

    # movement 
    def next(self, n=1):
        if self.state == 'list':
            self.test_list.move_list(n)
    def prev(self, n=1):
        if self.state == 'list':
            self.test_list.move_list(-n)

    # handle modality
    def modal_traceback(self):
        self.test_list.open_modal()
        if self.test_list.modal.traceback():
            self.state = 'traceback'
    def modal_output(self):
        self.test_list.open_modal()
        if self.test_list.modal.output():
            self.state = 'stdout'
    def modal_logging(self):
        self.test_list.open_modal()
        if self.test_list.modal.logging():
            self.state = 'logging'
    def modal_close(self):
        self.test_list.modal.close()
        self.state = 'list'

    # test related things
    def add_test(self, test_type, test, err):
        # update the status bar
        self.status_bar.add_test(test_type)

        if test_type != 'ok':
            self.test_list.add_test(test_type, test, err)
        self.test_list.dirty = True
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
            if not interface.handle_input(c):
                return

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

    # get and save exception before capture/logcapture get to it
    def formatError(self, test, err):
        test.exception = err[1]
        return err
    def formatFailure(self, test, err):
        test.exception = err[1]
        return err

    def addSuccess(self, test):
        self.test_queue.put( ('ok', test, None) )
    def addFailure(self, test, err):
        self.test_queue.put( ('fail', test, err) )
    def addError(self, test, err):
        self.test_queue.put( ('error', test, err) )

    ############################################################################
    # handle other boilerplate
    def finalize(self, result):
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
    # nose.main(plugins=[BoogerPlugin()])
    nose.main(addplugins=[BoogerPlugin()])

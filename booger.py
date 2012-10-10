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

from nose.plugins import Plugin

################################################################################
# windowing stuff

TEST_WIN_HEIGHT = 5

def get_new_tests(queue, counts, test_list):
    '''
    Retrieves tests from the queue, puts them in the right place
    Returns tuple:
      First, whether new tests were gotten
      Second, whether the output is finished
    '''
    try:
        s, t, e = queue.get(block=False)
    except Queue.Empty:
        return False, False
    # tests done
    if s is None and t is None and e is None:
        return False, True
    # keep getting until we're empty
    while 1:
        counts[s] += 1
        if e is not None:
            test_list.append((t,e))
        try:
            s, t, e = queue.get(block=False)
        except Queue.Empty:
            return True, False
        # tests done
        if s is None and t is None and e is None:
            return True, True

def init_status_bar(size, init_msg='Running tests...'):
    status_bar = curses.newwin(1,size[0])
    status_bar.attrset(curses.A_BOLD)
    status_bar.bkgdset(ord(' '), curses.color_pair(1))
    status_bar.clear()
    status_bar.addstr(0,0, init_msg + ' ' * (size[0] - len(init_msg) - 1))
    status_bar.refresh()
    return status_bar

def update_status_bar(status_bar, test_counts, tests_done):
    # update status bar
    status_bar.clear()
    ss = ['Tests Running...' if not tests_done else 'Tests Done!     ',
          'total: {0}'.format(sum([v for v in test_counts.values()]))]
    ss += ['{0}: {1}'.format(x,test_counts[x])
           for x in ['ok', 'error', 'fail']]
    counts = ' | '.join(ss)
    status_bar.addstr(0,0, counts)
    status_bar.refresh()

def init_test_win(test_area, size, test, test_number):
    win = test_area.derwin(TEST_WIN_HEIGHT, size[0],
                           TEST_WIN_HEIGHT*test_number, 0)
    return win

def update_test_win(win, size, test, err):
    win.clear()
    win.border()
    win.addstr(0, 5, str(test), curses.A_BOLD)
    # display error (type, exception, traceback)
    # get last tb_frame
    frame = err[2]
    while frame.tb_next:
        frame = frame.tb_next
    # get file failed in
    filename = frame.tb_frame.f_code.co_filename
    win.addstr(1, 1, filename[:size[0]-2])
    # get line of source code failed on
    f = open(filename)
    line = f.readlines()[frame.tb_frame.f_lineno-1]
    f.close()
    win.addstr(2, 1, line.rstrip()[:size[0]])
    # display what and how
    exception_name = err[1].__class__.__name__
    err_str = '{0}: {1}'.format(exception_name, err[1].message)[:size[0]-2]
    win.addstr(3, 1, err_str)

def curses_main(scr, test_queue):
    '''
    The curses loop
    Poll for input, new tests
    '''
    test_counts = {
        'ok': 0,
        'fail': 0,
        'error': 0,
    }
    # keep fail/error tests in a fixed list
    tests = []
    test_wins = {}

    curses.use_default_colors()
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    # wait for a character for only 0.1s
    curses.halfdelay(1)

    # size of the terminal
    size = None

    tests_done = False
    new_tests = False

    status_bar = None
    test_area = None
    cur_test = None
    prev_test = None

    detail_view = False
    detail_win = None

    try:
        while 1:
            # handle input
            c = scr.getch()
            prev_size = size
            size = scr.getmaxyx()[1], scr.getmaxyx()[0]
            if c == ord('q'):
                return
            elif c in [curses.KEY_DOWN, curses.KEY_UP, ord('n'), ord('p')]:
                prev_test = cur_test
                if cur_test is None:
                    cur_test = 0
                else:
                    cur_test += {curses.KEY_DOWN: 1, curses.KEY_UP: -1,
                                 ord('n'): 1, ord('p'): -1}[c]
                    cur_test %= len(tests)
            elif c == curses.KEY_ENTER:
                detail_view = not detail_view
            elif c == curses.KEY_RESIZE or size != prev_size:
                status_bar = None
                test_area = None
                new_tests = True
                test_wins = {}

            # handle any new tests
            if not tests_done:
                new_tests, tests_done = get_new_tests(test_queue, test_counts,
                                                      tests)

            # do some drawing
            if status_bar is None:
                status_bar = init_status_bar(size)
            if test_area is None:
                test_area = curses.newpad(2000,400)
                # initial refresh
                test_area.refresh(0,0, 1,0, size[1]-1,size[0]-1)
            if new_tests:
                update_status_bar(status_bar, test_counts, tests_done)
                # update test list
                for i in range(len(tests)):
                    t,e = tests[i]
                    if test_wins.get(i, None) is None:
                        win = init_test_win(test_area, size, t, i)
                        # windowing business
                        update_test_win(win, size, t, e)
                        test_wins[i] = win
                test_area.refresh(0,0, 1,0, size[1]-1,size[0]-1)
            ## !! ugh look at that repetition...
            if prev_test is not None:
                test_wins[prev_test].clear()
                test_wins[prev_test].bkgdset(ord(' '), curses.color_pair(0))
                update_test_win(test_wins[prev_test], size,
                                tests[prev_test][0], tests[prev_test][1])
                test_area.refresh(0,0, 1,0, size[1]-1,size[0]-1)
            if cur_test is not None:
                test_wins[cur_test].clear()
                test_wins[cur_test].bkgdset(ord(' '), curses.color_pair(1))
                update_test_win(test_wins[cur_test], size,
                                tests[cur_test][0], tests[cur_test][1])
                test_area.refresh(0,0, 1,0, size[1]-1,size[0]-1)
            if detail_view and cur_test is not None:
                if detail_win is None:
                    detail_win = curses.newpad(2000,400)
                    detail_win.addstr(0,0, 'HELLOWORSD')
                    detail_win.refresh(0,0, 0,0, size[1], size[0])
            elif detail_view is False and detail_win is not None:
                detail_win.refresh(0,0, 0,0, 0,0)
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
    def __init__(self, *args, **kwargs):
        super(BoogerPlugin, self).__init__(*args, **kwargs)

        self.test_queue = Queue.Queue()
        self.curses = threading.Thread(target=curses_run,
                                       args=(self.test_queue,))
        self.curses.start()

    ############################################################################
    # utils

    ############################################################################
    # test outcome handler
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
    nose.main(plugins=[BoogerPlugin()])

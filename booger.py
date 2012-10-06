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

    size = None
    new_tests = False
    status_bar = None
    test_area = None
    try:
        while 1:
            # handle input
            prev_size = size
            size = scr.getmaxyx()[1], scr.getmaxyx()[0]
            c = scr.getch()
            if c == ord('q'):
                return
            elif c == curses.KEY_RESIZE or size != prev_size:
                status_bar = None

            # handle any new tests
            try:
                s, t, e = test_queue.get(block=False)
                # tests done
                if s is None and t is None and e is None:
                    pass
                else:
                    test_counts[s] += 1
                    if e is not None:
                        tests.append((t, e))
                    new_tests = True
            except Queue.Empty:
                new_tests = False

            # do some drawing
            if status_bar is None:
                status_bar = curses.newwin(1,size[0])
                msg = 'Running tests...'
                status_bar.attrset(curses.A_BOLD)
                status_bar.bkgdset(ord(' '), curses.color_pair(1))
                status_bar.clear()
                status_bar.addstr(0,0, msg + ' ' * (size[0] - len(msg) - 1))
                status_bar.refresh()
            if test_area is None:
                test_area = curses.newpad(2000,400)
                test_area.refresh(0,0, 1,0, size[1]-1,size[0]-1)
            if new_tests:
                # update status bar
                status_bar.clear()
                ss = ['total: {0}'.format(sum([v for v in test_counts.values()]))]
                ss += ['{0}: {1}'.format(x,test_counts[x])
                       for x in ['ok', 'error', 'fail']]
                counts = ' | '.join(ss)
                status_bar.addstr(0,0, counts)
                status_bar.refresh()
                # update test list
                for i in range(len(tests)):
                    t,e = tests[i]
                    if test_wins.get(i, None) is None:
                        HEIGHT = 5
                        win = test_area.derwin(HEIGHT, size[0], HEIGHT*i, 0)
                        win.border()
                        win.addstr(0, 5, str(t), curses.A_BOLD)
                        # display error (type, exception, traceback)
                        # get last tb_frame
                        frame = e[2]
                        while frame.tb_next:
                            frame = frame.tb_next
                        # get file failed in
                        filename = frame.tb_frame.f_code.co_filename
                        win.addstr(1, 1, filename)
                        # get line of source code failed on
                        f = open(filename)
                        line = f.readlines()[frame.tb_frame.f_lineno-1]
                        win.addstr(2, 1, line[:-1])
                        # display what and how
                        exception_name = e[1].__class__.__name__
                        win.addstr(3, 1, '{0}: {1}'.format(exception_name,
                                                           e[1].message))
                        # windowing business
                        test_area.refresh(0,0, 1,0, size[1]-1,size[0]-1)
                        test_wins[i] = win
                scr.refresh()
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
        pass
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

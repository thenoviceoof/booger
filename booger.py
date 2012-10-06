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

    curses.use_default_colors()
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    # wait for a character for only 0.1s
    curses.halfdelay(1)

    size = None
    new_tests = False
    status_bar = None
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
                t = test_queue.get(block=False)
                test_counts[t[0]] += 1
                if t[0] != 'ok':
                    tests.append(t[1])
                new_tests = True
            except Queue.Empty:
                new_tests = False

            if status_bar is None:
                status_bar = curses.newwin(1,size[0])
                msg = 'Running tests...'
                status_bar.attrset(curses.A_BOLD)
                status_bar.bkgdset(ord(' '), curses.color_pair(1))
                status_bar.clear()
                status_bar.addstr(0,0, msg + ' ' * (size[0] - len(msg) - 1))
                status_bar.refresh()
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
                    t = tests[i]
                    scr.addstr(i+1, 0, str(t))
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
        self.test_queue.put(('ok', test))
    def addFailure(self, test, err):
        self.test_queue.put(('fail', test))
    def addError(self, test, err):
        self.test_queue.put(('error', test))

    ############################################################################
    # handle other boilerplate
    def finalize(self, result):
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

# just a test case
def test_test():
    assert False
def test_test_test():
    assert True

################################################################################
# main

if __name__ == "__main__":
    nose.main(plugins=[BoogerPlugin()])

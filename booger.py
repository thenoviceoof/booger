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
    tests = {
        'ok': [],
        'fail': [],
        'error': [],
    }

    curses.use_default_colors()
    try:
        # wait for a character for only 0.1s
        curses.halfdelay(1)
        while 1:
            # handle input
            c = scr.getch()
            if c == ord('q'):
                return
            # handle any new tests
            try:
                t = test_queue.get(block=False)
                tests[t[0]].append(t[1])
            except Queue.Empty:
                pass
            # refresh the page
            scr.addstr(0,0, "thing")
            scr.addstr(1,0, str(tests))
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

################################################################################
# main

if __name__ == "__main__":
    nose.main(plugins=[BoogerPlugin()])

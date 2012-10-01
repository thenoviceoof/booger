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
import curses

from nose.plugins import Plugin

################################################################################
# nose plugin

class BoogerPlugin(Plugin):
    def __init__(self, *args, **kwargs):
        self.tests = {
            'ok': [],
            'fail': [],
            'error': []
        }
        super(BoogerPlugin, self).__init__(*args, **kwargs)

    ############################################################################
    # utils

    def post_test(self):
        print '\r' + str([(n,len(t)) for n,t in self.tests.iteritems()]),

    ############################################################################
    # test outcome handler
    def addSuccess(self, test):
        self.tests['ok'].append(test)
        self.post_test()
    def addFailure(self, test, err):
        self.tests['fail'].append(test)
        self.post_test()
    def addError(self, test, err):
        self.tests['error'].append(test)
        self.post_test()

    def finalize(self, result):
        return None
    def report(self, stream):
        return False

    def setOutputStream(self, stream):
        self.stream = stream
        stream.write("FUCKKKKKKKKKKKk")
        class Dummy:
            def write(self, *arg):
                pass
            def writeln(self, *arg):
                pass
            def flush(self, *arg):
                pass
        return Dummy()

def test_test():
    import time
    time.sleep(2)
    assert False

def test_test2():
    import time
    time.sleep(2)
    assert False

################################################################################
# windowing stuff

class CursesManager(object):
    def __enter__(self):
        self.curses_scr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.curses_scr.keypad(1)
        return self.curses_scr
    def __exit__(self, type, value, traceback):
        self.curses_scr.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        if type is exceptions.KeyboardInterrupt:
            return True
        print type, value, traceback

################################################################################
# main

if __name__ == "__main__":
    nose.main(plugins=[BoogerPlugin()])

    # with CursesManager() as cur:
    #     while 1:
    #         cur.getch()
    #         cur.refresh()

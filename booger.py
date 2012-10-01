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
import threading
import exceptions

from nose.plugins import Plugin

################################################################################
# windowing stuff

def curses_main(scr):
    try:
        # wait for a character for only 0.1s
        curses.halfdelay(1)
        while 1:
            c = scr.getch()
            if c == ord('q'):
                return
            scr.refresh()
    except KeyboardInterrupt:
        return

class CursesInterface(threading.Thread):
    def __init__(self):
        super(CursesInterface, self).__init__()

        # self.curses_scr = curses.initscr()
        # curses.noecho()
        # curses.cbreak()
        # self.curses_scr.keypad(1)

    def run(self):
        curses.wrapper(curses_main)

    # def __del__(self):
    #     self.curses_scr.keypad(0)
    #     curses.nocbreak()
    #     curses.echo()
    #     curses.endwin()

################################################################################
# nose plugin

class BoogerPlugin(Plugin):
    def __init__(self, *args, **kwargs):
        self.tests = {
            'ok': [],
            'fail': [],
            'error': []
        }
        self.win = CursesInterface()
        super(BoogerPlugin, self).__init__(*args, **kwargs)
        self.win.start()

    ############################################################################
    # utils

    def post_test(self):
        pass
        # self.win.update_status([])

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
        self.win.join()
        del self.win
    def report(self, stream):
        pass
        # return False

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

def test_test():
    assert False

################################################################################
# main

if __name__ == "__main__":
    # nose.main(plugins=[BoogerPlugin()])
    c = CursesInterface()
    c.start()

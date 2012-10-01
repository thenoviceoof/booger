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
    def addSuccess(self, test):
        print test
    def addError(self, test, err):
        print test, err
    def addFailure(self, test, err):
        print test, err
    def finalize(self, result):
        return None
    def report(self, stream):
        return True

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
    nose.main(addplugins=[BoogerPlugin])
    # with CursesManager() as cur:
    #     while 1:
    #         cur.getch()
    #         cur.refresh()

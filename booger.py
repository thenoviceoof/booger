#!/usr/bin/python
################################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# <thenoviceoof> wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day,
# and you think this stuff is worth it, you can buy me a beer in
# return
# Nathan Hwang <thenoviceoof>
# ----------------------------------------------------------------------------
################################################################################

import sys
import curses
import subprocess

################################################################################
# utils

################################################################################
# nosetests output parser

NOSE_DIV_WIDTH = 70

class NosetestsParser(object):
    short_output = True

    def parse_short_output(s):
        
        return ''

    def parse_input(s):
        '''
        See if the input s contains
        - Short test output (.EF / other)
        - Long output (traceback / stdout / logging)
        '''
        if short_output:
            output = self.parse_short_output(s)
            print output
        return ''

# this is a test function, so we can run `nosetests booger.py` to get output
def run_test():
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
    parser = NosetestsParser()
    print ['nosetests'] + sys.argv[1:]
    p = subprocess.Popen(['nosetests'] + sys.argv[1:],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    for line in p.stdout:
        print line,
    # with CursesManager() as cur:
    #     while 1:
    #         cur.getch()
    #         cur.refresh()

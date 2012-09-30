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
import curses
import subprocess

################################################################################
# utils

################################################################################
# nosetests output parser

NOSE_DIV_WIDTH = 70
SHORT_MAPPING = {
    '.': 'ok',
    'E': 'error',
    'F': 'fail'
}

class NosetestsParser(object):
    short_output = True

    counts = {
        'ok': 0,
        'fail': 0,
        'error': 0
    }
    def parse_short_long_output(self, s):
        '''
        Try to parse apart the line as a -v test output
        Return test, status
        '''
        m = re.match(r'^(.*) \.\.\. (ok|FAIL|ERROR)$', s)
        if m is None:
            return None, None
        msg = m.group(1)
        status = m.group(2).lower()
        self.counts[status] += 1
        return msg, status
    def parse_short_short_output(self, s):
        '''
        Try to parse apart the line as a -v0 output (not an actual option)
        Return None
        '''
        m = re.match('^([.EF]+)$', s)
        if m is None:
            return
        ss = m.group(1)
        for s in ss:
            self.counts[SHORT_MAPPING[s]] += 1
    def parse_short_output(self, s):
        '''
        Takes a line of output
        Returns (test, status (ok, fail, error), end)
        '''
        if re.match('=' * NOSE_DIV_WIDTH, s):
            return None, None, True
        # get the test and it's status
        test, status = self.parse_short_long_output(s)
        if status:
            return test, status, False
        print test, status
        # this merely updates the counts
        self.parse_short_short_output(s)
        return None, None, False

    def parse_long_output(self, s):
        '''
        Take a line of output
        Do something else
        '''
        return ''

    def parse_input(self, s):
        '''
        See if the input s contains
        - Short test output (.EF / other)
        - Long output (traceback / stdout / logging)
        '''
        if self.short_output:
            test, status, end = self.parse_short_output(s)
            print s,
            if end:
                self.short_output = False
        else:
            output = self.parse_long_output(s)
        return ''

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
    args = ['nosetests'] + sys.argv[1:]
    if '-v' not in args:
        args.append('-v')
    print args
    p = subprocess.Popen(args,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    for line in p.stdout:
        parser.parse_input(line)
        # print line,
    # with CursesManager() as cur:
    #     while 1:
    #         cur.getch()
    #         cur.refresh()

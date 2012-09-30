#!/usr/bin/python
################################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# <thenoviceoof> wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day,
# and you think this stuff is worth it, you can buy me a beer in
# return
# Nathan Hwang <thenoviceoof>
################################################################################

from unittest import TestCase
from nose.tools import raises

################################################################################
# Nosetest parser

from booger import NOSE_DIV_WIDTH, NosetestsParser

########################################
# short tests

def short_output_end_test():
    '''
    Make sure we recognise the end of the short output
    '''
    parser = NosetestsParser()

    inp = '=' * 70
    test, status, end = parser.parse_short_output(inp)
    assert end == True

def short_output_short_test():
    '''
    Recognize -v0 test output
    '''
    parser = NosetestsParser()

    inp = 'EE...F'
    parser.parse_short_output(inp)
    assert parser.counts['ok'] == 3
    assert parser.counts['fail'] == 1
    assert parser.counts['error'] == 2

def short_output_ok_test():
    '''
    Recognize `msg ... ok` messages
    '''
    parser = NosetestsParser()

    msg = 'msg ... ok'
    test, status, end = parser.parse_short_output(msg)
    assert status == 'ok'
def short_output_fail_test():
    '''
    Recognize `msg ... FAIL` messages
    '''
    parser = NosetestsParser()

    msg = 'msg ... FAIL'
    test, status, end = parser.parse_short_output(msg)
    assert status == 'fail'
def short_output_error_test():
    '''
    Recognize `msg ... ERROR` messages
    '''
    parser = NosetestsParser()

    msg = 'msg ... ERROR'
    test, status, end = parser.parse_short_output(msg)
    assert status == 'error'

@raises()
def short_output_dots_test():
    '''
    A regression test, to make sure the ... (ok|ERROR|FAIL) ellipse
    doesn't match strange things
    '''
    raise NotImplemented

########################################
# 'long' tests (traceback, stdout, etc)


################################################################################
# we can't really test the curses stuff, so we don't try

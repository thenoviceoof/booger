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

################################################################################
# Nosetest parser

from booger import NOSE_DIV_WIDTH, NosetestsParser

class NosetestsParserTest(TestCase):
    def setUp(self):
        self.parser = NosetestsParser()

    def short_output_end_test(self):
        '''
        Make sure we recognise the end of the short output
        '''
        inp = '=' * 70
        out, end = self.parser.parse_short_output(inp)
        assert end == False
    def short_output_ok_test(self):
        '''
        Recognize `msg ... ok` messages
        '''
        msg = 'msg ... ok'
        out, end = self.parser.parse_short_output(msg)
        assert out == 'ok'
    def short_output_fail_test(self):
        '''
        Recognize `msg ... FAIL` messages
        '''
        msg = 'msg ... FAIL'
        out, end = self.parser.parse_short_output(msg)
        assert out == 'fail'
    def short_output_error_test(self):
        '''
        Recognize `msg ... ERROR` messages
        '''
        msg = 'msg ... ERROR'
        out, end = self.parser.parse_short_output(msg)
        assert out == 'error'

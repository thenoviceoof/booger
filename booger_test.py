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

from unittest import TestCase

################################################################################
# Nosetest parser

from booger import NOSE_DIV_WIDTH, NosetestsParser

class NosetestsParserTest(TestCase):
    def setUp(self):
        self.parser = NosetestsParser()
    def short_output_test(self):
        inp = '=' * 70
        out, end = self.parser.parse_short_output(inp)
        assert end == True

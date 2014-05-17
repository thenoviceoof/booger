################################################################################
# The MIT License (MIT)
#
# Copyright (c) <2012-2014> <thenoviceoof>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
################################################################################
# this file is mostly just as a target for booger to test on
#
# I don't recommend using this as an indicator for whether booger is
# broken or not

import sys
import time
import logging

log = logging.getLogger(__name__)

# test cases
def test_test():
    for i in range(200):
        print "Mu! {0}".format(i)
        print 'WHEE' * 100
    assert False
def test_test2():
    assert really_long_name_for_a_variable_oh_boy_this_is_long_wheeeeeeeeeeeeeeee == YOUR_MOTHER_IS_A_NICE_LADY

def test():
    assert True

def test_test_test_test_test_test_test_test_test_test_test_test_test_test_test():
    assert False

def test_test3():
    assert False
def test_test4():
    time.sleep(1)
    assert False

def test_test5():
    assert False
def test_test6():
    assert False
def test_test7():
    assert False
def test_test8():
    assert False
def test_test9():
    assert False
def test_test10():
    assert False

def mu_test():
    print "BANG BANG"

    sys.stderr.write("MU\n")
    log.debug('DANG')
    assert aoeu

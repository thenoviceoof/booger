import sys
import time
import logging

log = logging.getLogger(__name__)

# test cases
def test_test():
    assert False
def test_test2():
    assert False

def test_test_test():
    assert True

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

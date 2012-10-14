import sys
import logging

log = logging.getLogger(__name__)

# test cases
def test_test():
    assert False
def test_test2():
    assert False

def test_test_test():
    assert True

def mu_test():
    print "BANG BANG"

    sys.stderr.write("MU\n")
    log.debug('DANG')
    assert aoeu

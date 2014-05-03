from ui import *
import traceback

################################################################################
# example usage

status = Text('Tests something | ok: 0 | error: 0 | fail: 0', style='RB')
try:
    aoeu
except Exception as e:
    err = traceback.format_exc()[:-1]
exception = TextNoWrap(err)
def test(i):
    test = Box(exception,
               title_parts=[' F ', ' a_test%d ' % i],
               option_parts=[' Traceback ', ' stdOut '])
    return test

tests = List(test(1), test(2), test(3), test(4), test(5), test(6), test(7),
             test(8), test(9))

p = VerticalPile(status, tests)
p.current_window = p.windows[-1]

class App(Application):
    windows = {'default': p}

    def handle(self, key):
        if key == 'a':
            pass
        super(App, self).handle(key)

if __name__ == '__main__':
    App().run()

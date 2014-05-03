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
test = Box(exception,
           title_parts=[' F ', ' a_test '],
           option_parts=[' Traceback ', ' stdOut '])

p = VerticalPile(status, test, test, test, test, test, test, test, test)

class App(Application):
    windows = {'default': p}

    def handle(self, key):
        if key == 'a':
            pass
        super(App, self).handle(key)

if __name__ == '__main__':
    App().run()

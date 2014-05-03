from ui import *

################################################################################
# example usage

status = Text('Tests something | ok: 0 | error: 0 | fail: 0', style='RB')
try:
    aoeu
except Exception as e:
    err = str(e)
exception = TextNoWrap(err)
test = Box(exception,
           title_parts=[' F ', ' a_test '],
           option_parts=[' Traceback ', ' stdOut '])

p = VerticalPile(status, test)

class App(Application):
    windows = {'default': p}

    def handle(self, key):
        if key == 'a':
            pass
        super(App, self).handle(key)

if __name__ == '__main__':
    App().run()

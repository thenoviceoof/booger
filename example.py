from ui import *

################################################################################
# example usage

class App(Application):
    windows = {'default': TextBox('hello world\nglad you could swing by')}

    def handle(self, key):
        if key == 'a':
            pass
        super(App, self).handle(key)

if __name__ == '__main__':
    App().run()

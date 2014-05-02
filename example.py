from ui import *

################################################################################
# example usage

class App(Application):
    windows = {'default': Box(Text('hello world\nglad you could swing by'), title_parts=[' thing ', ' another '], option_parts=[' thing '])}

    def handle(self, key):
        if key == 'a':
            pass
        super(App, self).handle(key)

if __name__ == '__main__':
    App().run()

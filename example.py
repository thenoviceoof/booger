from ui import *

################################################################################
# example usage

class App(Application):
    windows = []

    def handle(self, key):
        if key == 'a':
            pass

if __name__ == '__main__':
    App().run()

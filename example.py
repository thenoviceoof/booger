from ui import *

################################################################################
# example usage

txt1 = Text(('hello world 1\n' * 2)[:-1])
txt2 = TextNoWrap(((('hello world 2 ' * 10) + '\n') * 10)[:-1])
b1 = Box(txt1, title_parts=[' plack ', ' dag '], option_parts=[' blah '])
b2 = Box(txt2, title_parts=[' doop '], option_parts=[' example ', ' auh '])
p = VerticalPile(b1, b2)

class App(Application):
    windows = {'default': p}

    def handle(self, key):
        if key == 'a':
            pass
        super(App, self).handle(key)

if __name__ == '__main__':
    App().run()

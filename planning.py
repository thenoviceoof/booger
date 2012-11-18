'''
Master plan:

MainWindow
 - Grid
   - Window (status bar)
   - WindowList (tests) (grid?)
     - Window (tracebacks)
 * Modal(s)
   - Traceback
     - Grid
       - WindowList (grid?)
         - Window (Current traceback frame)
       - Window (variables)
   - Stdout
   - Stderr
   - Logging

Break out for pdb
'''

################################################################################

class GUI(MainWindow):
    def __init__():
        self.children = [...]
        self.modals = [...]
        super.__init__()
    def loop(self):
        super().loop()

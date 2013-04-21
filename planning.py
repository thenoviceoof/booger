'''
Master plan:

MainWindow
 - Grid
   - Status Bar (TextWindow)
   - Tests (Grid)
     - Window (traceback borders)
       - TextWindow (traceback text)
 * Modal(s)
   - DetailModal
     * Modals
       - Traceback
         - Grid
           - Grid
             - Window (Current traceback frame)
           - Variables (TextWindow)
       - TextStdout (TextWindow)
       - TextStderr (TextWindow)
       - TextLogging (TextWindow)
   - SearchModal (Window)
     (override the __init__ to create an edit)
   - HelpModal
     - TextWindow

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

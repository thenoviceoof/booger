# The MIT License (MIT)
#
# Copyright (c) <2012-2014> <thenoviceoof>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
################################################################################

import re
import os
import sys
import nose
import Queue
import curses
import threading

from nose.plugins import Plugin
from unittest.case import SkipTest

from ui import *

################################################################################
# utils

def get_new_test(queue):
    s, t, e = queue.get(block=False)
    if e and e[0] is SkipTest:
        s = 'skip'
    return (s, t, e)

def get_new_tests(queue):
    '''
    Retrieves tests from the queue, puts them in the right place
    Returns a tuple:
        list of tuples (status, test object, err)
        whether tests are done (True if tests are done)
    '''
    try:
        s, t, e = get_new_test(queue)
    except Queue.Empty:
        return [], False
    # tests done
    if s is None and t is None and e is None:
        return [], True
    # keep getting until we're empty
    tests = []
    while 1:
        tests.append((s,t,e))
        try:
            s, t, e = get_new_test(queue)
        except Queue.Empty:
            return tests, False
        # tests done
        if s is None and t is None and e is None:
            return tests, True

def get_frames(tb_ptr):
    '''
    Gets tb_frames out of the dumb linked list format, into python lists
    '''
    frames = []
    while tb_ptr:
        frames.append(tb_ptr.tb_frame)
        tb_ptr = tb_ptr.tb_next
    return frames

################################################################################
# new windowing stuff

STATUS_BAR_RUNNING  = 'Tests Running...'
STATUS_BAR_FINISHED = 'Tests Done!     '

TEST_WIN_HEIGHT = 5

TRACEBACK_CODE_CONTEXT = 5
TRACEBACK_TEST_DEPTH = 3

class StatusBar(TextNoWrap):
    finished = False

    test_counts = {
        'ok': 0,
        'skip': 0,
        'fail': 0,
        'error': 0,
    }

    def render(self, size):
        status = []
        if self.finished:
            status += [STATUS_BAR_FINISHED]
        else:
            status += [STATUS_BAR_RUNNING]
        status += ['{0}: {1}'.format(x, self.test_counts[x])
                   for x in ['ok', 'skip', 'error', 'fail']]
        status_str = ' | '.join(status)
        self.text = status_str
        # render the updated text
        return super(StatusBar, self).render(size)

    def update(self, status):
        test_type = status[0].upper()
        mapping = {
            'S': 'skip',
            'F': 'fail',
            'E': 'error',
            }
        self.test_counts[mapping.get(test_type, 'ok')] += 1

class TestList(List):
    def _set_index(self, index):
        super(TestList, self)._set_index(index)
        for i,w in enumerate(self.windows):
            # need to reach into the pile.text/code to set the select
            w.window.selected = True if i == self.index else False

class TestCode(TextNoWrap):
    def render(self, size):
        lines, styles = super(TestCode, self).render(size)
        if not getattr(self, 'selected', None):
            # include the path, code, and exception
            lines = lines[-3:]
            styles = styles[-3:]
        return lines, styles

class Test(Box):
    def __init__(self, status, test, error):
        self.test = test
        exc_type, exception, traceback = error
        # grab the text
        exc_text = ''
        frames = get_frames(traceback)
        self.frames = frames
        if len(self.frames) >= TRACEBACK_TEST_DEPTH:
            for i in range(TRACEBACK_TEST_DEPTH):
                j = -TRACEBACK_TEST_DEPTH+i
                # get file failed in
                filename = frames[j].f_code.co_filename
                exc_text += filename + '\n'
                # get line of source code failed on
                with open(filename) as f:
                    code = f.readlines()[frames[j].f_lineno-1]
                exc_text += code
        # display what and how
        exc_name = exc_type.__name__
        msg = exception.message if hasattr(exception, 'message') else ''
        exc_text += '{0}: {1}'.format(exc_name, msg)
        exc_window = TestCode(exc_text)

        # title
        titles = [' %s ' % status[0].upper(), ' %s ' % test]
        # options
        options = [' Traceback ',
                   ' stdOut '
                   if getattr(self.test, 'capturedOutput', None) else
                   u'\u2500' * 8,
                   ' Logging '
                   if getattr(self.test, 'capturedLogging', None) else
                   u'\u2500' * 9]
        super(Test, self).__init__(exc_window,
                                   title_parts=titles,
                                   option_parts=options)

    def handle(self, key):
        signal = super(Test, self).handle(key)
        if signal is None:
            if key in ('t', 'T'):
                tb = self.frames
                return ('window', 'traceback', {'traceback': tb,
                                                'type': 'traceback',
                                                'title': str(self.test)})
            if key in ('o', 'O'):
                text = getattr(self.test, 'capturedOutput', None)
                if not text:
                    return None  # don't do anything for no output
                return ('window', 'output', {'text': text,
                                             'type': 'stdout',
                                             'title': str(self.test)})
            if key in ('l', 'L'):
                text = getattr(self.test, 'capturedLogging', None)
                if not text:
                    return None  # don't do anything for no output
                text = '\n'.join(text)  # comes back as a list
                return ('window', 'output', {'text': text,
                                             'type': 'logging',
                                             'title': str(self.test)})
        return signal

class Modal(Box):
    force = True

    @property
    def type(self):
        return self.title_parts[0]

    @type.setter
    def type(self, type):
        self.title_parts[0] = ' %s ' % type

    @property
    def title(self):
        return self.title_parts[1]

    @title.setter
    def title(self, title):
        self.title_parts[1] = ' %s ' % title

class TracebackList(List):
    def _set_index(self, index):
        super(TracebackList, self)._set_index(index)
        for i,w in enumerate(self.windows):
            # need to reach into the pile.text/code to set the select
            w.windows[1].selected = True if i == self.index else False

class TracebackCode(Text):
    def render(self, size):
        lines, styles = super(TracebackCode, self).render(size)
        if not getattr(self, 'selected', None):
            lines = lines[-1:]
            styles = styles[-1:]
        return lines, styles

class TracebackVars(Box):
    def __init__(self, *args, **kwargs):
        self.vars = Text('', indent=' ' * 14)
        kwargs.update({'title_parts': [' Variables '], 'force': True})
        super(TracebackVars, self).__init__(self.vars, *args, **kwargs)

    def render(self, size):
        w,h = size
        # munge so we can trim the decorations
        lines, styles = super(TracebackVars, self).render((w+2,h+1))
        # trim lower lines
        lines = lines[:-1]
        styles = styles[:-1]
        # trim sides
        lines = [l[1:-1] for l in lines]
        styles = [[(s[0],s[1]-1,s[2]-1) if s else s for s in line]
                  for line in styles]
        # add bold to the top
        styles[0].append(('B', 0, w))
        return lines, styles

    def display_vars(self, frame):
        local_vars = getattr(frame, 'f_locals', None)
        global_vars = getattr(frame, 'f_globals', None)
        # filter out __special__ vars
        if global_vars:
            global_vars = dict([(k,v) for k,v in global_vars.iteritems()
                                if not k.startswith('__')])
        text = ''
        # DRY
        for name, variables in [('Local Variables', local_vars),
                                ('Global Variables', global_vars)]:
            # do we need new lines?
            if not text.endswith('\n') and text:
                text += '\n\n'
            text += '### {0}\n'.format(name)
            var_lines = ['{0}: {1}'.format(vname.ljust(12), vvalue)  # 12 is magic
                         for vname, vvalue in variables.iteritems()]
            text += '\n'.join(var_lines)
        self.vars.text = text

class TracebackModal(Modal):
    _traceback = None

    def __init__(self):
        self.frame_windows = TracebackList()
        self.var_disp = TracebackVars()
        self.split_pane = VerticalPileEqual(self.frame_windows)
        super(TracebackModal, self).__init__(self.split_pane,
                                             title_parts=['', ''],
                                             option_parts=[' Variables '])

    @property
    def traceback(self):
        return self._traceback

    @traceback.setter
    def traceback(self, traceback):
        self.frame_windows.clear()
        self._traceback = traceback
        for frame in traceback:
            # get code
            path = frame.f_code.co_filename
            with open(path) as f:
                start_line = frame.f_lineno - TRACEBACK_CODE_CONTEXT
                end_line = frame.f_lineno
                lines = f.readlines()[start_line:end_line]
                lines = [l.rstrip() for l in lines]
                code = (('%d|' % i).rjust(5) + l
                        for i,l in zip(range(start_line, end_line), lines))
                code = '\n'.join(code)
            # windows
            path_window = Text(path, style='B')
            code_window = TracebackCode(code)
            line = VerticalPile(path_window, code_window)
            self.frame_windows.add(line)
            # keep frame around for future reference
            line.frame = frame

    def handle(self, key):
        signal = super(TracebackModal, self).handle(key)
        if signal is None:
            if key in ('v', 'V'):
                if len(self.split_pane.windows) == 1:
                    self.split_pane.windows += (self.var_disp,)
                    # populate the vars
                    current_frame = self.frame_windows.current_window.frame
                    self.var_disp.display_vars(current_frame)
                else:
                    self.split_pane.windows = self.split_pane.windows[:1]
                # var shown/hidden, redraw
                return 'redraw'
        # redo the vars if you move frames
        if signal is None or signal == 'redraw':
            if key in ('n', curses.KEY_UP, 'p', curses.KEY_DOWN):
                if len(self.split_pane.windows) > 1:
                    current_frame = self.frame_windows.current_window.frame
                    self.var_disp.display_vars(current_frame)
                return 'redraw'
        return signal

class OutputModal(Modal):
    def __init__(self):
        text_lines = TextLineNumbers('')
        #! planned
        # text_lines = Search(Scrollable(text_lines), lambda x: x.lines)
        text_lines = Scrollable(text_lines)
        super(OutputModal, self).__init__(text_lines, title_parts=['', ''])

    @property
    def text(self):
        return self.window.window.text

    @text.setter
    def text(self, text):
        self.window.window.text = text

class App(Application):
    # make default windows
    status = StatusBar('Starting up...', style='RB')
    tests = TestList()
    pile = VerticalPile(status, tests, index=1)
    # make modal windows
    traceback_modal = TracebackModal()
    output_modal = OutputModal()

    windows = {
        'default': pile,
        'output': output_modal,
        'traceback': traceback_modal,
        }

    tests_done = False

    def __init__(self, test_queue, *args, **kwargs):
        self.test_queue = test_queue
        super(App, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        try:
            super(App, self).run(*args, **kwargs)
        finally:
            # be responsive to quits (thread.interrupt_main seems to not work)
            # otherwise, test thread can continue to execute
            if not self.tests_done:
                # use exit code 2 here: 1 is for any failed tests (presumed)
                os._exit(2)

    def handle(self, key):
        result = super(App, self).handle(key)
        # pull the latest test, update everyone
        if not self.tests_done:
            tests, done = get_new_tests(self.test_queue)
            # add new tests
            for status, test, error in tests:
                self.status.update(status)
                if status not in ('ok', 'skip'):
                    self.tests.add(Test(status, test, error))
            # mark done
            if done:
                self.status.finished = True
                self.tests_done = True
            # redraw
            self.render()

def curses_run(test_queue):
    App(test_queue).run()

################################################################################
# nose plugin

class BoogerPlugin(Plugin):
    '''
    A pretty curses-based nose frontend
    '''
    enabled = False
    name = 'booger'
    score = 3000

    def __init__(self, *args, **kwargs):
        super(BoogerPlugin, self).__init__(*args, **kwargs)

        self.test_queue = Queue.Queue()

    ############################################################################
    # options
    def options(self, parser, env):
        '''
        Register booger's commandline options
        '''
        parser.add_option(
            '--booger', action = 'store_const',
            default = False, const = True, dest = 'booger',
            help = 'Display captured output in a curses interface')
    def configure(self, options, conf):
        self.conf = conf
        self.enabled = options.booger

        if self.enabled:
            self.curses = threading.Thread(target=curses_run,
                                           args=(self.test_queue,))
            self.curses.start()

    ############################################################################
    # test outcome handler

    # get and save exception before capture/logcapture get to it
    def formatError(self, test, err):
        test.exception = err[1]
        return err
    def formatFailure(self, test, err):
        test.exception = err[1]
        return err

    def addSuccess(self, test):
        self.test_queue.put( ('ok', test, None) )
    def addFailure(self, test, err):
        self.test_queue.put( ('fail', test, err) )
    def addError(self, test, err):
        self.test_queue.put( ('error', test, err) )

    ############################################################################
    # handle other boilerplate
    def finalize(self, result):
        self.test_queue.put( (None,None,None) )
        self.curses.join()
    def report(self, stream):
        # stop normal report stdout from printing
        return False
    def setOutputStream(self, stream):
        self.stream = stream
        class Dummy:
            def write(self, *arg):
                pass
            def writeln(self, *arg):
                pass
            def flush(self, *arg):
                pass
        return Dummy()

################################################################################
# main

if __name__ == "__main__":
    # nose.main(plugins=[BoogerPlugin()])
    nose.main(addplugins=[BoogerPlugin()])

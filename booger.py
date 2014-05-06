#!/usr/bin/python
################################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# <thenoviceoof> wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day,
# and you think this stuff is worth it, you can buy me a beer in
# return
# Nathan Hwang <thenoviceoof>
################################################################################

import re
import sys
import nose
import Queue
import curses
import threading
import exceptions
import curses.textpad
from StringIO import StringIO

from nose.plugins import Plugin

from ui import *

################################################################################
# utils

def get_new_tests(queue):
    '''
    Retrieves tests from the queue, puts them in the right place
    Returns a tuple:
        list of tuples (status, test object, err)
        whether tests are done (True if tests are done)
    '''
    try:
        s, t, e = queue.get(block=False)
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
            s, t, e = queue.get(block=False)
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
# windowing stuff

class TestWindow(object):
    def __init__(self, screen, test_list, test_status, test, err,
                 *args, **kwargs):
        self.screen = screen
        self.window = test_list.subwin(1,1, 0,0)

        self.selected = False
        self.test_status = test_status
        self.test = test
        self.err = err
        self.y = 0

        self.frames = get_frames(self.err[2])

        super(TestWindow, self).__init__(*args, **kwargs)

    def update(self, y=None):
        '''
        We don't actually call refresh, since we expect the TestList
        to be a pad that needs to call refresh itself
        '''
        # store the current position
        if y is None:
            y = self.y
        else:
            self.y = y
        traceback_lines = {True: 5, False: 1}[self.selected]
        if traceback_lines > len(self.frames):
            traceback_lines = len(self.frames)
        lines = 3 + traceback_lines * 2

        size = get_size(self.screen)
        self.window.mvderwin(y, 0)
        self.window.resize(lines, size[0])

        self.window.clear()
        self.window.box()

        self.window.addstr(0, 2, ' %s ' % self.test_status[0].upper(),
                           curses.A_BOLD)
        self.window.addstr(0, 7, str(self.test)[:size[0]-8], curses.A_BOLD)

        # display error (type, exception, traceback)
        for i in range(traceback_lines):
            j = -traceback_lines+i
            # get file failed in
            filename = self.frames[j].f_code.co_filename
            self.window.addstr(1 + i*2, 1, filename[:size[0]-2])
            # get line of source code failed on
            f = open(filename)
            line = f.readlines()[self.frames[j].f_lineno-1]
            f.close()
            self.window.addstr(2 + i*2, 1, line.rstrip()[:size[0]-2])
        # display what and how
        exception = self.test.exception
        exception_name = exception.__class__.__name__
        err_str = '{0}: {1}'.format(exception_name, exception)[:size[0]-2]
        self.window.addstr(lines-2, 1, err_str)

        # add controls
        if self.selected:
            options = ['T_raceback']
            if self.test.capturedOutput:
                options.append('stdO_ut')

            if self.test.capturedLogging:
                options.append('L_ogging')

            acc = 3
            for opt in reversed(options):
                opts = opt.split('_')
                acc += len(opts[0]) + len(opts[1]) + 2
                self.window.addstr(lines-1, size[0]-acc, opts[0][:-1])
                self.window.addstr(lines-1, size[0]-acc + len(opts[0][:-1]),
                                   opts[0][-1], curses.A_BOLD)
                self.window.addstr(lines-1,
                                   size[0]-acc + len(opts[0]),
                                   opts[1])

        return lines

    def select(self):
        self.selected = True
        self.window.bkgdset(ord(' '), curses.color_pair(1))
        self.update()
    def deselect(self):
        self.selected = False
        self.window.bkgdset(ord(' '), curses.color_pair(0))
        self.update()


class TestModal(object):
    def __init__(self, screen, *args, **kwargs):
        self.screen = screen
        self.window = curses.newpad(MAX_PAD_HEIGHT, MAX_PAD_WIDTH)

        # pointers to the test/err currently being displayed
        self.test = None
        self.err = None

        self.opened = False

        # gui detritus
        self._scroll = 0
        self.len = 0
        self.contents = []

        # search specific things
        self.search_term = None

    # mode switching
    def traceback(self):
        self.type = 'traceback'
        self.update()
        return True
    def output(self):
        if self.test.capturedOutput:
            self.type = 'stdout'
            self.update()
            return True
        else:
            return False
    def logging(self):
        if self.test.capturedLogging:
            self.type = 'logging'
            self.update()
            return True
        else:
            return False

    # update modes
    def update_traceback(self):
        self.contents = []

        size = get_size(self.screen)
        self.frames = get_frames(self.err[2])

        # display traceback
        acc = 1
        context = 5
        for frame in self.frames:
            # get file failed in
            filename = frame.f_code.co_filename
            # display less context for libraries
            if re.match(r'(^/usr/lib.*|.*/\.local/lib/.*)', filename):
                context = 0
            else:
                context = 5
            self.window.bkgdset(ord(' '), curses.color_pair(1))
            self.window.addstr(acc, 0, filename[:size[0]-2])
            self.window.bkgdset(ord(' '), curses.color_pair(0))
            # get line of source code failed on
            f = open(filename)
            lines = f.readlines()
            ln_from, ln_to = (frame.f_lineno - 1 - context, frame.f_lineno)
            ls = lines[ln_from:ln_to]
            if ln_from < 0:
                ls = [''] * (-ln_from) + ls
            f.close()
            # display lines + context
            for j in range(len(ls)):
                l = ls[j].rstrip()
                i = 0
                while l:
                    self.contents.append(l[:size[0]-2])
                    self.window.addstr(acc + i + 1, 1, l[:size[0]-2])
                    if i > 0:
                        self.window.addstr(acc + i + 1, 0, '>')
                    l = l[size[0]-1:]
                    i += 1
                acc += i
            if context:
                self.window.addstr(acc, 0, '*')
            acc += 2
        self.len = acc
    def update_stdout(self):
        self.contents = []

        lines = self.test.capturedOutput.split('\n')
        size = get_size(self.screen)
        acc = 0
        for l in lines:
            while l:
                self.contents.append(l[:size[0]-1])
                line = l[:size[0]-1]
                # abortive attempt at highlighting things
                if self.search_term and self.search_term in line:
                    self.window.bkgdset(ord(' '), curses.color_pair(1))
                    self.window.addstr(acc,0, line)
                    self.window.bkgdset(ord(' '), curses.color_pair(0))
                else:
                    self.window.addstr(acc,0, line)
                l = l[size[0]-1:]
                acc += 1
        self.len = acc
    def update_logging(self):
        self.contents = []

        lines = self.test.capturedLogging
        size = get_size(self.screen)
        acc = 0
        for l in lines:
            while l:
                self.contents.append(l[:size[0]-1])
                self.window.addstr(acc,0, l[:size[0]-1])
                l = l[size[0]-1:]
                acc += 1
        self.len = acc
    # master update
    def update(self):
        if not self.opened:
            return

        size = get_size(self.screen)
        self.window.clear()

        if self.type == 'traceback':
            self.update_traceback()
        elif self.type == 'stdout':
            self.update_stdout()
        elif self.type == 'logging':
            self.update_logging()

        # draw the scroll bar
        if self.len > size[1]:
            for i in range(size[1]):
                self.window.addstr(self._scroll + i,size[0]-1, '|')
            total = self.len - (size[1] - 1)
            d = int((float(self._scroll) / total) * (size[1]-1))
            self.window.addstr(self._scroll+d, size[0]-1, '#', curses.A_BOLD)

        self.window.refresh(self._scroll,0, 0,0, size[1]-1, size[0]-1)

    # movement
    def scroll(self, n=1):
        size = get_size(self.screen)
        self._scroll += n
        self._scroll %= self.len - (size[1] - 1)
    def start(self):
        self._scroll = 0
    def end(self):
        self._scroll = 0
        self.scroll(-1)

    # search
    def search(self, string):
        if string:
            string = string[:-1]
        # update the search term so we can highlight it
        self.search_term = string
        for i in range(self.len - self._scroll - 1):
            if string in self.contents[self._scroll + i + 1]:
                self._scroll += i + 1
                break

    # open/closing
    def open(self, test, err):
        self._scroll = 0
        self.test = test
        self.err = err
        self.opened = True
    def close(self):
        self.opened = False
        # stop searching
        self.search_term = None

################################################################################
# new windowing stuff

STATUS_BAR_RUNNING  = 'Tests Running...'
STATUS_BAR_FINISHED = 'Tests Done!     '

TEST_WIN_HEIGHT = 5

class StatusBar(TextNoWrap):
    finished = False

    test_counts = {
        'ok': 0,
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
                   for x in ['ok', 'error', 'fail']]
        status_str = ' | '.join(status)
        self.text = status_str
        # render the updated text
        return super(StatusBar, self).render(size)

    def update(self, status):
        test_type = status[0].upper()
        mapping = {
            'F': 'fail',
            'E': 'error',
            }
        self.test_counts[mapping.get(test_type, 'ok')] += 1

class Test(Box):
    def __init__(self, status, test, error):
        self.test = test
        exc_type, exception, traceback = error
        # grab the text
        exc_text = ''
        traceback_lines = 1
        frames = get_frames(traceback)
        self.frames = frames
        for i in range(traceback_lines):
            j = -traceback_lines+i
            # get file failed in
            filename = frames[j].f_code.co_filename
            exc_text += filename + '\n'
            # get line of source code failed on
            with open(filename) as f:
                code = f.readlines()[frames[j].f_lineno-1]
            exc_text += code
        # display what and how
        exc_name = test.exception.__class__.__name__
        exc_text += '{0}: {1}'.format(exc_name, test.exception)
        exc_window = TextNoWrap(exc_text)

        # title
        titles = [' %s ' % status[0].upper(), ' %s ' % test]
        # options
        options = [' Traceback ',
                   ' stdOut ' if self.test.capturedOutput else u'\u2500' * 8,
                   ' Logging ' if self.test.capturedLogging else u'\u2500' * 9]
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
                text = self.test.capturedOutput
                if not text:
                    return None  # don't do anything for no output
                return ('window', 'output', {'text': text,
                                             'type': 'stdout',
                                             'title': str(self.test)})
            if key in ('l', 'L'):
                text = self.test.capturedLogging
                if not text:
                    return None  # don't do anything for no output
                text = '\n'.join(text)  # comes back as a list
                return ('window', 'output', {'text': text,
                                             'type': 'logging',
                                             'title': str(self.test)})
        return signal

class Modal(Box):
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

class TracebackModal(Modal):
    _traceback = None

    def __init__(self):
        self.frame_windows = List()
        super(TracebackModal, self).__init__(self.frame_windows,
                                             title_parts=['', ''])

    @property
    def traceback(self):
        return self._traceback

    @traceback.setter
    def traceback(self, traceback):
        self.frame_windows.clear()
        log(traceback)
        log(dir(traceback[0]))

        self._traceback = traceback
        for frame in traceback:
            # get code
            path = frame.f_code.co_filename
            with open(path) as f:
                code = ('%d|' % frame.f_lineno).rjust(5)
                code += f.readlines()[frame.f_lineno-1][:-1].rstrip()
            # windows
            path_window = TextNoWrap(path)
            code_window = TextNoWrap(code)
            line = VerticalPile(path_window, code_window)
            self.frame_windows.add(line)

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
    tests = List()
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

    def handle(self, key):
        result = super(App, self).handle(key)
        # pull the latest test, update everyone
        if not self.tests_done:
            tests, done = get_new_tests(self.test_queue)
            # add new tests
            for status, test, error in tests:
                self.status.update(status)
                if status != 'ok':
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
    Something
    '''
    enabled = False
    name = 'booger'
    score = 3000

    def __init__(self, *args, **kwargs):
        super(BoogerPlugin, self).__init__(*args, **kwargs)

        self.test_queue = Queue.Queue()
        self.curses = threading.Thread(target=curses_run,
                                       args=(self.test_queue,))
        self.curses.start()

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

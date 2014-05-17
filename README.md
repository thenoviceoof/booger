booger
================================================================================
Eats the output of a nosetests run, and put it into a nice curses
interface, instead of letting nosetests throw a tsunami of output into
stdout after all the tests finish.


SCREENSHOTS
--------------------------------------------------------------------------------

![Booger main listing](https://raw.githubusercontent.com/thenoviceoof/booger/docs/docs/page1.png)

![Booger variable view](https://raw.githubusercontent.com/thenoviceoof/booger/docs/docs/page2.png)


INSTALLATION
--------------------------------------------------------------------------------
`booger` is on [pypi](https://pypi.python.org/pypi/booger):

    pip install booger


USAGE
--------------------------------------------------------------------------------
To use `booger`, you can use either invoke it as a plugin, or call the
wrapping script.

    nosetests --booger YOUR_TESTS

    booger YOUR_TESTS

Commands:
 - Move with `up`/`down` arrow keys, or `n`/`p` (next/previous) keys
 - On the main testcase listing, with a selected testcase, press:
   - `t` for traceback
   - `o` for stdout
   - `l` for logging output
 - In the traceback view, press:
   - `v` to toggle the current frame's variable view
 - On the stdout/logging views, `page up`/`page down` also work, as
   you would expect


MOTIVATION
--------------------------------------------------------------------------------
If you've ever threw nosetests on a big test suite, and a few of those
tests happened to be broken with a ton of logging going on (as it
should be), then you're going to have a bad time scrolling around
trying to find the most pertinent information first.

Booger is an effort to give you the best information first, with more
information easily available, quickly.

To this end, booger will progressively show you which tests are
failing with the last line of the error's traceback along with the
actual error, and make the stdout, logging, and the full traceback
with the variables at each frame available.


Questions that will probably be asked frequently
--------------------------------------------------------------------------------
 - Q: Really? Toilet Humor?
 - A: Yup

 - Q: Where can I report bugs?
 - A: Please use the [project's github bug
   tracker](https://github.com/thenoviceoof/booger/issues?state=open)


LICENSE
--------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<thenoviceoof> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you
think this stuff is worth it, you can buy me a beer in return
Nathan Hwang <thenoviceoof>

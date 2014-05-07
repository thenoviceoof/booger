booger
================================================================================
Eats the output of a nosetests run, and put it into a nice curses
interface.


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
actual error, and make the stdout, logging, and full traceback
available.

Eventually, booger aims to allow searching through all the collected
output (which should also include stderr), have variables lists
attached to the tracebacks, allow you to drop into a python
debugger. Swanky, no?


Questions that will probably be asked frequently
--------------------------------------------------------------------------------
 - Q: Really? Toilet Humor?
 - A: Yup


LICENSE
--------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<thenoviceoof> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you
think this stuff is worth it, you can buy me a beer in return
Nathan Hwang <thenoviceoof>

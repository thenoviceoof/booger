booger
======
Eats the output of a nosetests run, and put it into a nice curses
interface, instead of letting nosetests throw a tsunami of output into
stdout after all the tests finish.


SCREENSHOTS
-----------

.. image:: https://raw.githubusercontent.com/thenoviceoof/booger/docs/docs/page1.png
   :alt: Booger main listing

.. image:: https://raw.githubusercontent.com/thenoviceoof/booger/docs/docs/page2.png
   :alt: Booger variable view

INSTALLATION
------------
``booger`` is on `pypi <https://pypi.python.org/pypi/booger>`_:

::

    pip install booger


USAGE
-----
To use ``booger``, you can use either invoke it as a plugin, or call the
wrapping script.

::

    nosetests --booger YOUR_TESTS

    booger YOUR_TESTS

Commands:

- Move with ``up`` / ``down`` arrow keys, or ``n`` / ``p``
  (next/previous) keys
- On the main testcase listing, with a selected testcase, press:

  * ``t`` for traceback
  * ``o`` for stdout
  * ``l`` for logging output

- In the traceback view, press:

  * ``v`` to toggle the current frame's variable view

- On the stdout/logging views, ``page up``/``page down`` also work, as
  you would expect
- ``q`` quits the current activity, or closes the curses interface


MOTIVATION
----------
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
------------------------------------------------
 - Q: Really? Toilet Humor?
 - A: Yup

 - Q: Where can I report bugs?
 - A: Please use the `project's github bug tracker
   <https://github.com/thenoviceoof/booger/issues?state=open>`_


LICENSE
-------
The MIT License (MIT)

Copyright (c) <2012-2014> <thenoviceoof>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

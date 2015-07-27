gisht
=====

*Gists in the shell*


|Version| |Development Status| |Python Versions| |License| |Build Status|

.. |Version| image:: https://img.shields.io/pypi/v/gisht.svg?style=flat
    :target: https://pypi.python.org/pypi/gisht
    :alt: Version
.. |Development Status| image:: https://img.shields.io/pypi/status/gisht.svg?style=flat
    :target: https://pypi.python.org/pypi/gisht/
    :alt: Development Status
.. |Python Versions| image:: https://img.shields.io/pypi/pyversions/gisht.svg?style=flat
    :target: https://pypi.python.org/pypi/gisht
    :alt: Python versions
.. |License| image:: https://img.shields.io/pypi/l/gisht.svg?style=flat
    :target: https://github.com/Xion/gisht/blob/master/LICENSE
    :alt: License
.. |Build Status| image:: https://img.shields.io/travis/Xion/gisht.svg?style=flat
    :target: https://travis-ci.org/Xion/gisht
    :alt: Build Status


With *gisht*, you can run scripts published as GitHub gists with a single command::

    gisht Xion/git-today

Behind the scenes, *gisht* will fetch the gist, cache it locally, and run its code.
Magic!


Installation
~~~~~~~~~~~~

Install *gisht*  using *pip*, the Python package manager::

    pip install gisht

Depending on how the Python interpreter is configured on your system,
you may need to use ``sudo`` to install *gisht* globally.
(Or use ``virtualenv``).

For TAB completion of gist names, add the following to your ``~/.bashrc``::

    eval $(register-python-autocomplete gisht)

or ``~/.zshrc``::

    autoload bashcompinit
    bashcompinit
    eval $(register-python-autocomplete gisht)


Usage
~~~~~

If you want to pass arguments, put them after ``--`` (two dashes)::

    gisht Octocat/greet -- "Hello world" --cheerful

If the gist doesn't have a proper shebang (e.g. ``#!/usr/bin/python``),
*gisht* will look at any file extensions and try to deduce how to run the gist.

You can also use ``-w`` (``--which``) option
and call the interpreter explicitly::

    python `gisht -w Octocat/badgist`

For more options, type::

    gisht --help


Contributing
~~~~~~~~~~~~

Contributions are of course very welcome!
If you need some ideas, just head to the issue tracker.

This should get you started on the actual development::

    pip install -r requirements-dev.txt
    tox

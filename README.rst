gisht
=====

*Gists in the shell*


|Version| |Development Status| |Python Versions| |License| |Build Status|

.. |Version| image:: https://img.shields.io/pypi/v/gisht.svg?style=flat
    :target: https://pypi.python.org/pypi/gisht
    :alt: Version
.. |Development Status| image:: https://pypip.in/status/gisht/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/gisht/
    :alt: Development Status
.. |Python Versions| image:: https://pypip.in/py_versions/gisht/badge.svg?style=flat
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


Installation
~~~~~~~~~~~~

Install *gisht* from PyPI using PIP::

    pip install gisht

To follow Python's best practices, it's recommended that you place *gisht*
in its own virtualenv -- for example::

    virtualenv /usr/local/gisht
    source /usr/local/gisht/bin/activate
    pip install gisht

For convenience, you can then alias it inside your ``~/.bash_aliases``, ``~/.zshrc``,
etc.::

    alias gisht='/usr/local/gisht/bin/gisht.py'

A more convenient installation procedure will be likely offered in the future.


Usage
~~~~~

Supply the gist in the *<owner>/<name>* format, as you can see it on its GitHub page::

    gisht Octocat/foo

Any arguments after `--` will be passed to the gist executable::

    gisht Octocat/greet -- "Hello world" --cheerful

For more options, type::

    gisht --help


Notes
~~~~~

Right now, this project is in very early stages. If you want to help,
look for all the numerous ``TODO``\ s scattered about and try bringing their number down :)

This should get you started on the development::

    pip install -r requirements-dev.txt
    tox

Contributions welcome!

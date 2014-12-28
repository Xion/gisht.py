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
Magic!


Installation
~~~~~~~~~~~~

Automatic
---------

You can use the ``install.sh`` script to install *gisht* automatically::

    curl -L https://github.com/Xion/gisht/raw/master/install.sh | sh

It will place *gisht* in ``/usr/local`` directory and expose ``gisht`` command
to all users in the system (assuming ``/usr/local/bin`` is in their ``$PATH``).

Manual
------

Alternatively, you can install *gisht*  manually using PIP::

    pip install gisht

To follow Python's best practices, it's recommended that you place *gisht*
in its own virtualenv -- for example::

    virtualenv /usr/local/gisht
    source /usr/local/gisht/bin/activate
    pip install gisht

For convenience, you can then alias it inside your ``~/.bash_aliases``, ``~/.zshrc``,
etc.::

    alias gisht='/usr/local/gisht/bin/gisht'

The automatic installation script essentially does all of the above.


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

Right now, this project is in early stages. `ROADMAP.rst` file contains some ideas
on where it could be headed in the near and/or further future.

If you want to help, your best bet is to look for all the numerous ``TODO``\ s
scattered about the code case, and try to bring their number down :)

This should get you started on the development::

    pip install -r requirements-dev.txt
    tox

Contributions welcome!

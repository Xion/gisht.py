Roadmap
=======

Interface improvements
~~~~~~~~~~~~~~~~~~~~~~

* ~/.gishtrc support
* Logging & -v/--verbose + -q/--quiet modes
* Correcting misspelt gist names
* Autocompletion of gists (from local cache)
* Autocompletion of gist names after `user/` is typed
  (first from local cache and then GitHub)

Private gists
~~~~~~~~~~~~~

* Getting user login / password, how to store them?
* Define "default" user, so we can only supply gist name?

Improved gist management
~~~~~~~~~~~~~~~~~~~~~~~~

* More robust download ("install") process
* Forcing remote => aliasing => anonymous gist support
* Gist updating?
* Gist removal? (from cache/bin)

Execution on steroids
~~~~~~~~~~~~~~~~~~~~~

* Detecting interpreter from file extension
* Or even from syntax

Crazy things
------------

* Parse import / require / etc. statements to figure out dependencies
  and download them, installing within virtualenv / rvm / etc. for the gist
* Compile and run C / C++ / Java if the code has main() function / method

Other gist actions
~~~~~~~~~~~~~~~~~~

* -s/--star for starring gists (requires acting as user, see Private gists)
* -c/--comment for leaving comments (as above)

Project health
~~~~~~~~~~~~~~

* More tests
* Move development off `master` branch into named feature branches

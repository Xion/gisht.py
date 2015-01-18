Roadmap
=======

Interface improvements
~~~~~~~~~~~~~~~~~~~~~~

* ~/.gishtrc support
* Correcting misspelt gist names

Private gists
~~~~~~~~~~~~~

* Getting user login / password, how to store them?
* Define "default" user, so we can only supply gist name?

Improved gist management
~~~~~~~~~~~~~~~~~~~~~~~~

* Aliasing => anonymous gist support
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

Distribution
~~~~~~~~~~~~

* Create a Debian package
* Create a Homebrew formula
* Create an RPM package

Project health
~~~~~~~~~~~~~~

* Move development off `master` branch into named feature branches

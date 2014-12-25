#!/bin/sh

# gisht
# Installation script

# Usage -- one of:
#   curl -L https://github.com/Xion/gisht/raw/master/install.sh | sh
#   git clone https://github.com/Xion/gisht.git && cd gisht && ./install.sh


APP='gisht'

VIRTUALENV_DIR="/usr/local/$APP"
RUNNER_SCRIPT="/usr/local/bin/$APP"


main() {
    require python "Python not found -- aborting!"
    require pip "PIP not found -- please fix your Python installation!"

    ensure_virtualenv
    install_python_package

    create_runner_script
}

ensure_virtualenv() {
    # unless we're already inside a Python virtualenv, we need to create one
    if [ -z "$VIRTUAL_ENV" ]; then
        require virtualenv

        virtualenv "$VIRTUALENV_DIR"
        source "$VIRTUALENV_DIR/bin/activate"
    else
        log "WARN: Installing within existing virtualenv: $VIRTUAL_ENV"
    fi
}

install_python_package() {
    # either install the package from current directory
    # or get it directly from PyPI
    if [ -f "./$APP" ] || [ -f "./$APP/__init__.py" ]; then
        pip install -e .
    else
        pip install --upgrade $APP
    fi
}

create_runner_script() {
    # create simple wrapper script that activates the virtualenv
    # and runs the application
    cat >"$RUNNER_SCRIPT" <<- END
        #!/bin/sh
        source "$VIRTUALENV_DIR/bin/activate"
        $APP "\$@"
    END
    chmod a+x "$RUNNER_SCRIPT"
}


# Utility functions

require() {
    # Require for an external program to exist, abort the script if not found
    local prog="$1"
    local msg="${2-$prog not found, aborting.}"
    if ! which "$prog" >/dev/null; then
        log "FATAL: $msg"
        exit 1
    fi
}

log() {
    local fmt="$1" ; shift
    printf >&2 "\n>>> $fmt\n" "$@"
}

main "$@"

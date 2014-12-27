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
    if which "$APP" >/dev/null; then
        log "FATAL: $APP is already installed."
        exit
    fi

    require python "Python not found -- aborting!"
    require pip "PIP not found -- please fix your Python installation!"

    ensure_virtualenv
    install_python_package

    create_runner_script

    log "INFO: Installation complete."
    log "$APP should be available under \`$APP\` command"
    log "(If not, make sure $RUNNER_SCRIPT is in \$PATH, or create an alias)."
}

ensure_virtualenv() {
    # unless we're already inside a Python virtualenv, we need to create one
    if [ -z "$VIRTUAL_ENV" ]; then
        require virtualenv

        log "INFO: Creating new virtualenv for $APP..."
        virtualenv --quiet "$VIRTUALENV_DIR" --no-site-packages
        source "$VIRTUALENV_DIR/bin/activate"
    else
        log "WARN: Installing within existing virtualenv: $VIRTUAL_ENV"
    fi
}

install_python_package() {
    log "INFO: Installing $APP Python package..."

    # either install the package from current directory
    # or get it directly from PyPI
    if [ -f "./$APP/__init__.py" ]; then
        pip install -e .
    else
        # perform clean install by removing any existing installations first
        pip uninstall $APP --log-file /dev/null >/dev/null  # quiet!
        pip install $APP
    fi
}

create_runner_script() {
    log "INFO: Creating runner script in %s..." "$(dirname "$RUNNER_SCRIPT")"

    # create simple wrapper script that activates the virtualenv
    # and runs the application
    cat >"$RUNNER_SCRIPT" <<END
#!/bin/sh
source "$VIRTUAL_ENV/bin/activate"
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
    printf >&2 ">>> $fmt\n" "$@"
}


main "$@"

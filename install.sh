#!/bin/sh

# gisht
# Installation script

# Usage -- one of:
#   curl -L https://github.com/Xion/gisht/raw/master/install.sh | sh
#   git clone https://github.com/Xion/gisht.git && cd gisht && ./install.sh


APP='gisht'

DEFAULT_VENV_DIR="/usr/local/$APP"
FALLBACK_VENV_DIR="~/.$APP/venv"

DEFAULT_RUNNER_SCRIPT="/usr/local/bin/$APP"
FALLBACK_RUNNER_SCRIPT=""

_fallback_used=""


main() {
    if which "$APP" >/dev/null; then
        log "WARN: $APP is already installed; will reinstall."
    fi

    require python "Python not found -- aborting!"
    require pip "PIP not found -- please fix your Python installation!"

    ensure_virtualenv
    install_python_package

    create_runner_script

    local runner_script="$(get_runner_script_path)"
    log "INFO: Installation complete."
    log "$APP should be available through \`$APP\` command"
    log "(If not, %s, or %s)" \
        "make sure $(dirname "$runner_script") is in \$PATH" \
        "create an alias to $runner_script"
}


# virtualenv creation

ensure_virtualenv() {
    # unless we're already inside a Python virtualenv, we need to create one
    if [ -z "$VIRTUAL_ENV" ]; then
        require virtualenv

        local venv_dir="$(get_venv_dir)"
        log "INFO: Creating new virtualenv for $APP..."
        virtualenv --quiet "$venv_dir" --no-site-packages
        source "$venv_dir/bin/activate"
    else
        log "WARN: Installing within existing virtualenv: $VIRTUAL_ENV"
    fi
}

get_venv_dir() {
    # if we cannot put virtualenv in a "global" place,
    # use a directory under user's $HOME as a fallback
    local venv_dir="$DEFAULT_VENV_DIR"
    if [ -n "$_fallback_used" ] || [ ! -w "$(dirname "$venv_dir")" ]; then
        venv_dir="$FALLBACK_VENV_DIR"
        mkdir -p "$(dirname "$venv_dir")"
        _fallback_used="true"
    fi
    echo "$venv_dir"
}

install_python_package() {
    log "INFO: Installing $APP Python package..."

    # perform clean install by removing any existing installations first
    yes | pip uninstall $APP --log-file /dev/null >/dev/null  # quiet!

    # either install the package from current directory
    # or get it directly from PyPI
    if [ -f "./$APP/__init__.py" ]; then
        pip install -e .
    else
        pip install $APP
    fi
}


# Runner script generation

create_runner_script() {
    local runner_script="$(get_runner_script_path)"
    log "INFO: Creating runner script in %s..." "$(dirname "$runner_script")"

    # create simple wrapper script that activates the virtualenv
    # and runs the application
    cat >"$runner_script" <<END
#!/bin/sh
source "$VIRTUAL_ENV/bin/activate"
$APP "\$@"
END
    chmod a+x "$runner_script"
}

get_runner_script_path() {
    # similary to get_venv_dir(), fallvack to user's $HOME location
    # if we don't have permissions to write into the "global" one
    local runner_script="$DEFAULT_RUNNER_SCRIPT"
    if [ -n "$_fallback_used" ] || [ ! -w "$(dirname "$runner_script")" ]; then
        runner_script="$FALLBACK_RUNNER_SCRIPT"
        mkdir -p "$(dirname "$runner_script")"
        _fallback_used="true"
    fi
    echo "$runner_script"
}


# Utility functions

require() {
    # Require for an external program to exist, abort the script if not found
    local prog="$1"
    local msg="${2-$prog not found, aborting.}"
    if ! which "$prog" >/dev/null; then
        log "FATAL: $msg"
        exit 69  # EX_UNAVAILABLE
    fi
}

log() {
    local fmt="$1" ; shift
    printf >&2 ">>> $fmt\n" "$@"
}


main "$@"

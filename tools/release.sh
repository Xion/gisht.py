#!/bin/sh

# Release automation script

set -e


main() {
    ensure_release_version

    "$(dirname "$0")/homebrew.sh"
    upload_to_pypi

    add_git_tag
    git_push
}


# Version management

ensure_release_version() {
    local version="$(get_version)"

    # check if the version number is a one that doesn't
    # indicate a valid release, e.g. "0.5-dev" instead of just "0.5"
    if ! matches "$version" "^[0-9]+(\\.[0-9]+)+$" ; then
        fatal "Invalid version number: %s" "$version"
    fi
}

get_version() {
    cat gisht/__init__.py | \
    sed -E -n "/__version__ = [\"'](.+)[\"']/s//\1/p"
}


# Package management

upload_to_pypi() {
    local version="$(get_version)"
    log "Uploading version $version to PyPI..."

    local pypi_out="$(python setup.py sdist upload 2>&1)"
    if matches "$pypi_out" 'Upload failed' ; then
        echo 1>&2 "$pypi_out"
        fatal "Failed to upload version $version to PyPI"
    fi

    log "PyPI upload complete."
}


# Git

add_git_tag() {
    local version="$(get_version)"

    # TODO(xion): overwrite previous tag, if any
    if ! git tag "$version"; then
        fatal "Failed to add Git tag for version %s" "$version"
    fi
}

git_push() {
    # TODO(xion): remove previously exisiting tag on the remote, if any
    if ! git push && git push --tags ; then
        fatal "Failed to push the release upstream"
    fi
}


# Utility functions

matches() {
    # Check if given string matches a(n extended) regular expression.
    local s="$1"
    local re="$2"
    echo "$s" | grep -E "$2" >/dev/null
}

fatal() {
    local fmt="$1" ; shift
    log "FATAL: $fmt" "$@"
    exit 1
}

log() {
    local fmt="$1" ; shift
    printf >&2 ">>> $fmt\n" "$@"
}


main "$@"

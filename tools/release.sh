#!/bin/sh

# Release automation script

set -e


HOMEBREW_FORMULA='gisht.rb'


main() {
    require poet "Development packages not installed, aborting."

    create_homebrew_formula
}


create_homebrew_formula() {
    log "Creating Homebrew formula..."

    local tmpfile="/tmp/$HOMEBREW_FORMULA"
    rm -f "$tmpfile"

    # generate the formula using homebrew-pypi-poet
    cat << EOF >"$tmpfile"
# gisht :: Homebrew formula definition
# AUTOGENERATED BY ./tools/release.sh -- DO NOT EDIT!

EOF
    poet --formula gisht >>"$tmpfile"

    # commit it if it's got any changes
    if different "$tmpfile" "./$HOMEBREW_FORMULA" ; then
        mv -f "$tmpfile" "./$HOMEBREW_FORMULA"

        log "Formula created, committing..."

        # TODO(xion): include version in the commit
        git add "./$HOMEBREW_FORMULA"
        if git commit --edit --message="Regenerate Homebrew formula" ; then
            log "New Homebrew formula generated & committed."
        else
            log "Aborted at committing Homebrew formula"
            exit 1
        fi
    else
        log "Formula already up to date."
    fi
}


# Utility functions

different() {
    # Compare two files and return 0 if they differ.
    local f1="$1"
    local f2="$2"

    if [ ! -f "$f1" ] && [ ! -f "$f2" ]; then
        return 1
    fi

    if [ -f "$f1" ] && [ ! -f "$f2" ]; then
        return 0
    fi
    if [ ! -f "$f1" ] && [ -f "$f2" ]; then
        return 0
    fi

    cmp "$f1" "$f2" 2>&1 >/dev/null && return 1 || return 0
}

require() {
    # Require for an external program to exist, abort the script if not found
    local prog="$1"
    local msg="${2-$prog not found, aborting.}"
    if ! which "$prog" >/dev/null; then
        log "FATAL: $msg\n"
        exit 1
    fi
}

log() {
    local fmt="$1" ; shift
    printf >&2 ">>> $fmt\n" "$@"
}


main "$@"

#!/bin/sh

# Script for testing autocompletion functionality
# Invokes `gisht` like the shell would have done when querying for completions
#
# Usage::
#
#     $ ./tools/autocomplete.sh PREFIX
#
# where PREFIX is what user would've typed after `gisht ` before hitting <TAB>.

PROGNAME=gisht
TEST_ARGS="$@"

export _ARC_DEBUG=1
export COMP_LINE="$PROGNAME $TEST_ARGS"
export COMP_POINT=31
export _ARGCOMPLETE=1

# TODO(xion): fd/9 is debug log; add some flag to redirect it somewhere
# rather than just silencing by default
$PROGNAME 8>&1 9>/dev/null | tr '\v' '\n'
echo ''

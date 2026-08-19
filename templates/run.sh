#!/bin/sh
# Regenerate + verify. Usage: ./run.sh [config.yaml]
FC=${FREECADCMD:-/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd}
CONFIG=${1:-config.example.yaml} OUT_DIR=${OUT_DIR:-output} \
  "$FC" "$(dirname "$0")/generator_template.FCMacro" 2>&1 | grep -v "NOTICE\|%)"

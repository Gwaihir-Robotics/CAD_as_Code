#!/bin/sh
# Regenerate and check the razor head. Usage: ./run.sh [config.yaml]
#   TIER=mild|medium|med_aggr|all   PROCESS=prototype|production
#   EXPORT_DIR=exports              also refresh the curated exports (PASS only)
# Exits 0 only when every build prints RESULT PASS.
# FreeCAD: $FREECADCMD if set, else the macOS app bundle, freecadcmd on PATH,
# or the newest ~/Applications/FreeCAD_*.AppImage (Linux).
DIR=$(cd "$(dirname "$0")" && pwd)
CONFIG=${1:-$DIR/config.yaml}
FC=$FREECADCMD
MAC=/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd
[ -n "$FC" ] || { [ -x "$MAC" ] && FC=$MAC; }
[ -n "$FC" ] || FC=$(command -v freecadcmd || command -v FreeCADCmd)
[ -n "$FC" ] || FC=$(ls "$HOME"/Applications/FreeCAD_*.AppImage 2>/dev/null | tail -n 1)
[ -n "$FC" ] || { echo "FreeCAD not found; set FREECADCMD to freecadcmd or the AppImage" >&2; exit 1; }
case $FC in *.AppImage) set -- "$FC" freecadcmd ;; *) set -- "$FC" ;; esac
LOG=$(mktemp)
cd "$DIR" || exit 1
CONFIG=$CONFIG OUT_DIR=${OUT_DIR:-$DIR/output} \
  "$@" "$DIR/razor_head.FCMacro" 2>&1 | grep -v "NOTICE\|%)\|qt.qpa\|^FreeCAD 1\|^(C) 20\|LGPL2\|\*\*\*\|Transfer\|WorkSession\|Step File Name\|^Recompute\|^.\[[0-9;]*m$" | tee "$LOG"
if grep -q "RESULT PASS" "$LOG" && ! grep -q "RESULT FAIL" "$LOG"; then rm -f "$LOG"; exit 0; fi
rm -f "$LOG"; exit 1

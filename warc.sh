#!/bin/bash

# https://github.com/webrecorder/replayweb.page
# https://replayweb.page/

if [ -z "$1" ] || [ ! -d "$1" ]; then
  echo "Ha de pasar como parámetro un directorio donde se van a guardar los resultados"
  exit 1
fi

OUT="$(realpath "$1")"
DIR="$(realpath $(dirname "$0"))"
LNK="$DIR/data/links.txt"
URL="https://raw.githubusercontent.com/15hack/web-backup/main/out/links.txt"

exe() {
  CMD=$(echo "\$ $@" | sed "s|$HOME|~|g")
  echo "$CMD"
  "$@"
}
wgt() {
  # --warc-cdx
  WOUT=$(echo "$@" | sed 's|.*--warc-file=||' | cut -d' ' -f1)
  exe wget --no-check-certificate --no-verbose \
  --delete-after --no-directories \
  --page-requisites \
  --mirror \
  --no-warc-keep-log \
  --output-file="$WOUT.log" \
  --warc-cdx \
  "$@"
  echo "Exit code: $?" >> "$WOUT.log"
}

TMP="$(mktemp -d)"
if [ ! -f "$LNK" ]; then
  LNK="$TMP/links.txt"
  wget -q -O "$LNK" "$URL"
  if [ $? -ne 0 ]; then
    echo "Error descargando $URL"
    exit 0
  fi
fi

echo "# WKS: $TMP"
cd "$TMP"


FRM=$(wc -l "$LNK" | cut -d' ' -f1)
FRM="${#FRM}"
FRM="%${FRM}s"

function do_wgt {
  if [ -f "$1" ]; then
    INFL="$1"
    NAME=$(basename "$INFL" | sed 's|\.[^\.]*$||')
    echo "# $LNKS"
    wgt --input-file="$INFL" --warc-file="$OUT/$NAME"
  else
    URL="$1"
    DOM=$(echo "$URL" | cut -d'/' -f3)
    echo "# $DOM"
    wgt --warc-file="$OUT/$DOM" "$URL"
  fi
}


rm -R "$OUT"
mkdir -p "$OUT"
# Ocultar carpeta destino en los logs
ln -s "$OUT" out
OUT="out"

cat "$LNK" | grep -E "^https?://[^/]*" -oh | sort | uniq -c | sort -n -r | sed 's|^[ 0-9]*||' | awk -F'/' '!visited[$3]++' > out/15M.txt
do_wgt out/15M.txt

#cat out/15M.txt | while read URL; do
#  do_wgt "$URL"
#done

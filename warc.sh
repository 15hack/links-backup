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
if [ ! -f "$LNK" ]; then
  wget -q -O "$LNK" "$URL"
  if [ $? -ne 0 ]; then
    echo "Error descargando $URL"
    exit 0
  fi
fi
exe() {
  CMD=$(echo "\$ $@" | sed "s|$HOME|~|g")
  echo "$CMD"
  "$@"
}


TMP="$(mktemp -d)"
echo "# WKS: $TMP"
cd "$TMP"

FRM=$(wc -l "$LNK" | cut -d' ' -f1)
FRM="${#FRM}"
FRM="%${FRM}s"

function do_dom {
  URL="$1"
  DOM=$(echo "$URL" | cut -d'/' -f3)
  WARC1="$OUT/$DOM.warc"
  WARC2="$OUT/$DOM.warc.gz"
  WGLOG="$OUT/${DOM}.log"
  echo "# $DOM"
  exe wget --no-check-certificate --no-verbose \
  --delete-after --no-directories \
  --page-requisites \
  --mirror \
  --warc-cdx --warc-file="$OUT/$DOM" \
  --output-file="$WGLOG" \
  "$URL"
  if [ $? -eq 0 ]; then
    rm "$WGLOG"
  else
    if [ -f "$WARC1" ]; then
      rm "$WARC1"
    elif [ -f "$WARC2" ]; then
      rm "$WARC2"
    fi
  fi
}

rm -R "$OUT"
mkdir -p "$OUT"
cat "$LNK" | grep -E "^https?://[^/]*" -oh | sort | uniq -c | sort -n -r | sed 's|^[ 0-9]*||' | awk -F'/' '!visited[$3]++' | while read URL; do
  do_dom "$URL"
done

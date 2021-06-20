#!/bin/bash

# https://github.com/webrecorder/replayweb.page
# https://replayweb.page/

OUT="warc"

if [ "$1" == "--log" ]; then
  if [ ! -d "$OUT" ]; then
    echo "$OUT no es un directorio"
    exit 1
  fi
  find "$OUT" -name "*.cdx"  -print0 |
  while IFS= read -r -d '' CDX; do
      echo "# $(basename $CDX)"
      grep -ohE " https?://[^/]+" "$CDX" | sed 's|.*//||' | sort | uniq -c
  done
  exit 0
fi

if [ -e "$OUT" ]; then
  if [ ! -d "$OUT" ]; then
    echo "$OUT existe y no es un directorio"
    exit 1
  fi
  if [ ! -z "$(ls -A "$OUT")" ]; then
    echo "$OUT ha de estar vacio"
    exit 1
  fi
fi

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

URL="https://raw.githubusercontent.com/15hack/web-backup/main/out/links.txt"
ROT="https://15hack.github.io/web-backup/out/links.html"
DIR="$(pwd)"
mkdir -p "$OUT"

TMP="$(mktemp -d)"
echo "# WKS: $TMP"
echo "# OUT: $OUT"
cd "$TMP"

# Ocultar carpeta destino en los logs
OUT="$DIR/$OUT"
ln -s "$OUT" out
OUT="out"

LNK="$TMP/links.txt"
wget -q -O "$LNK" "$URL"
if [ $? -ne 0 ]; then
  echo "Error descargando $URL"
  exit 1
fi

function do_wgt {
  if [ "$1" == "$ROT" ]; then
    DOMS=$(cat "$LNK" | cut -d'/' -f3 | sort | uniq | tr '\n' ',' | sed 's|,$||')
    echo "# $1"
    wgt --span-hosts --domains="$DOMS" --warc-file="$OUT/15M" "$ROT"
  elif [ -f "$1" ]; then
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

do_wgt "$ROT"

#grep -E "/mailman/listinfo$" "$LNK" > mail.txt
#grep -vE "/mailman/(pipermail|listinfo)" "$LNK" > webs.txt

#cat mail.txt | sort | uniq -c | sort -n -r | sed 's|^[ 0-9]*||' | awk -F'/' '!visited[$3]++' > out/15M.txt
#cat webs.txt | grep -E "^https?://[^/]*" -oh | sort | uniq -c | sort -n -r | sed 's|^[ 0-9]*||' | awk -F'/' '!visited[$3]++' >> out/15M.txt
#do_wgt out/15M.txt

#cat out/15M.txt | while read URL; do
#  do_wgt "$URL"
#done

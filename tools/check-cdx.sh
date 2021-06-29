#!/bin/bash

URL="https://raw.githubusercontent.com/15hack/web-backup/main/out/links.txt"
CDX="$1"

if [ -z "$CDX" ] || [ ! -f "$CDX" ]; then
  echo "$CDX no exite"
  exit 1
fi

CDX="$(realpath "$CDX")"

cd $(mktemp -d)
curl -s "$URL" | sed -E 's|^https?://||' | sed 's|/$||' | sort > links.txt
grep -Eoh " http[^ ]+" "$CDX" | sed 's|^ *||' | sed -E 's|^https?://||' | sed 's|/$||' | sort > cdx.txt
comm -23 links.txt cdx.txt

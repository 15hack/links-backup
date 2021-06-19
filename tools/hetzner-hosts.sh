#!/bin/bash
RIP="192.168.52.102"
URL="https://raw.githubusercontent.com/15hack/web-backup/main/out/links.txt"

wget -q -O "links.txt" "$URL"
grep -E "/mailman/listinfo$" links.txt > mail.txt
grep -vE "/mailman/(pipermail|listinfo)" links.txt > webs.txt

cat mail.txt | sort | uniq -c | sort -n -r | sed 's|^[ 0-9]*||' | awk -F'/' '!visited[$3]++' > 15M.txt
cat webs.txt | grep -E "^https?://[^/]*" -oh | sort | uniq -c | sort -n -r | sed 's|^[ 0-9]*||' | awk -F'/' '!visited[$3]++' >> 15M.txt

cat 15M.txt | while read URL; do
  DOM=$(echo "$URL" | cut -d'/' -f3)
  if [ "$DOM" == "www.tomalatele.tv" ]; then
    echo "${RIP} $DOM"
    continue
  fi
  ST=$(curl -kLs -o /dev/null -w "%{http_code}" "$URL")
  if [ "$ST" != "200" ]; then
    ST=$(curl --resolve "${DOM}:443:${RIP}" --resolve "${DOM}:80:${RIP}" -kLs -o /dev/null -w "%{http_code}" "$URL")
    if [ "$ST" == "200" ]; then
      echo "${RIP} $DOM"
    else
      echo "# $DOM status_code = $ST"
    fi
  fi
done

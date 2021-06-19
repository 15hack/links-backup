#!/bin/bash
RIP="192.168.52.102"
curl -s "https://raw.githubusercontent.com/15hack/web-backup/main/out/links.txt" | \
cut -d'/' -f3 | sort | uniq | while read DOM; do
  if [ "$DOM" == "www.tomalatele.tv" ]; then
    echo "${RIP} $DOM"
    continue
  fi
  ST=$(curl -kLs -o /dev/null -w "%{http_code}" "http://$DOM")
  if [ "$ST" != "200" ]; then
    ST=$(curl --resolve "${DOM}:443:${RIP}" --resolve "${DOM}:80:${RIP}" -kLs -o /dev/null -w "%{http_code}" "http://$DOM")
    if [ "$ST" == "200" ]; then
      echo "${RIP} $DOM"
    else
      echo "# $DOM status_code = $ST"
    fi
  fi
done

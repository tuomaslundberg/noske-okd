#!/usr/bin/env bash

# ── OKD: register arbitrary UID in /etc/passwd ───────────────────────────────
# OKD assigns a random UID not present in /etc/passwd.  Processes that call
# getpwuid() (lighttpd logging, Python's pwd module) need a valid entry.
# /etc/passwd was made group-writable in Dockerfile.okd (chmod g=u), and
# our effective GID under OKD's restricted SCC is always 0, so this write works.
if ! whoami &> /dev/null; then
  if [ -w /etc/passwd ]; then
    echo "nseuser:x:$(id -u):0:NSE user:/home/user:/sbin/nologin" >> /etc/passwd
  fi
fi
# ─────────────────────────────────────────────────────────────────────────────

if [ ! "$(ls -A /usr/lib/python3.9/dist-packages/bonito)" ];
then cp -R /usr/lib/python3.9/site-packages/bonito.init/* /usr/lib/python3.9/dist-packages/bonito
fi
if [ ! "$(ls -A /var/www/crystal)" ];
then cp -R /var/www/crystal.init/* /var/www/crystal
     sed -i "s~URL_BONITO: \"http://localhost/~URL_SKE_LI: \"about:blank\", URL_CA: \"about:blank\", URL_BONITO: \"${BROWSER_URL_BONITO:-}/~g" /var/www/crystal/config.js
fi
for corp in $CORPLIST; do
path=$(corpinfo -p $corp)
if [ ! -d $path ] || [ ! "$(ls -A $path)" ]
  then mkdir -p $path; compilecorp $corp
  fi
done
exec 3>&1
exec /usr/sbin/lighttpd -f /etc/lighttpd/lighttpd.conf -D

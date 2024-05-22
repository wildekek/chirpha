#!/bin/sh
# vim:sw=4:ts=4:et

#set -e

#echo aaa$1
#exec nginx -g "daemon off;"
#tempio -conf /data/options.json -template /etc/nginx.conf.gtpl -out /tmp/nginx.conf
cp /etc/nginx.conf.gtpl /tmp/nginx.conf
nginx -T -c /tmp/nginx.conf

exec nginx -c /tmp/nginx.conf
#echo bbb$1

#!/bin/sh
DIR=$( cd "$(dirname "$0")" ; pwd -P )
. $DIR/env.sh
curl --retry 0 --socks5-hostname $SOCKS_PROXY --connect-timeout 30 $1| grep -E -o '[0-9a-zA_Z]+\.onion'

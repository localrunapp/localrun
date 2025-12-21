#!/bin/sh
set -e

# Ensure log directory exists and has proper permissions
mkdir -p /data/localrun/logs
chown -R localrun:localrun /data/localrun

# Start supervisor
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

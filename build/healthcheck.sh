#!/bin/sh
# Health check for both services
wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1
wget --no-verbose --tries=1 --spider http://localhost:3006/ || exit 1

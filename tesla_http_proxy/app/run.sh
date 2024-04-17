#!/bin/ash
set -e

echo "Configuration Options are:"
echo SERVER_MODE=$SERVER_MODE
echo CONFIG_BASE=$CONFIG_BASE
echo "-------------------------"
echo CLIENT_ID=$CLIENT_ID
echo "CLIENT_SECRET=Not Shown"
echo DOMAIN=$DOMAIN
echo REGION=$REGION

if [ $SERVER_MODE == 1 ]; then
  echo "Serving Tesla public key"
  python3 /app/keyserver.py --config-base "$CONFIG_BASE"
elif [ $SERVER_MODE == 2 ]; then
  echo "Starting temporary Python app for authentication flow"
  python3 /app/run.py --client-id "$CLIENT_ID" --client-secret "$CLIENT_SECRET" --domain "$DOMAIN" --region "$REGION" --config-base "$CONFIG_BASE"
elif [ $SERVER_MODE == 3 ]; then
  echo "Starting Tesla HTTP Proxy"
  tesla-http-proxy -key-file $CONFIG_BASE/tesla/com.tesla.3p.private-key.pem -cert $CONFIG_BASE/tls/cert.pem -tls-key $CONFIG_BASE/tls/key.pem -port 8099 -host 0.0.0.0 -verbose
fi

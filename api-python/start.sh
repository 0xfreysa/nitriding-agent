#!/bin/sh

nitriding -fqdn example.com -ext-pub-port 443 -intport 8080 -wait-for-app &
echo "[sh] Started nitriding."

sleep 1


# echo "📦 installing nodejs & pnpm"
# curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
#     apt-get install -y nodejs && \
#     npm install -g pnpm
    
pnpm --version

echo "📦 installing pnpm packages"
cd /bin/freysa-autonomous-project
pnpm install
 

echo "🚀 starting python server"
cd /bin
python3 service.py
echo "[sh] Python server started."

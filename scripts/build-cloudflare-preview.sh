#!/usr/bin/env bash
set -euo pipefail

# Build a static Cloudflare Pages preview from the feature branch.
rm -rf dist
mkdir -p dist/image/achievement
cp preview/index.html dist/index.html
cp -R public_html/image/achievement/. dist/image/achievement/
touch dist/_headers
cat > dist/_headers <<'EOF'
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: DENY
EOF

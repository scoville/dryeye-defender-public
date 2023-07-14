#!/usr/bin/env bash
set -Eeuxo pipefail
VERSION=$1
sed -i.bak "s/version =.*/version = \"${VERSION}\"/g" pyproject.toml
sed -i.bak "s/Version:.*/Version: ${VERSION}/g" deb_build/DEBIAN/control
sed -i.bak "s/'CFBundleShortVersionString': '.*'/'CFBundleShortVersionString': '${VERSION}'/g" pyinstaller_build.spec
sed -i.bak "s/version='.*'/version='${VERSION}'/g" pyinstaller_build.spec

#!/usr/bin/env bash
set -Eeuxo pipefail
VERSION=$1
sed -i "s/version =.*/version = \"${VERSION}\"/g" pyproject.toml
sed -i "s/Version:.*/Version: ${VERSION}/g" deb_build/DEBIAN/control
sed -i "s/'CFBundleShortVersionString': '.*'/'CFBundleShortVersionString': '${VERSION}'/g" pyinstaller_build.spec
sed -i "s/version='.*'/version='${VERSION}'/g" pyinstaller_build.spec

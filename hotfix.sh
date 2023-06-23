#!/usr/bin/env bash
set -Eeuxo pipefail

VERSION=$1

if [ -z "$1" ]
  then
    echo "No argument supplied for required version"
    exit 1
fi

# ensure you are on branch: hotfix/2.0.2  (e.g.  git flow hotfix start 2.0.2)

sed -i "s/version.*/version=\"${VERSION}\"\,/g" setup.py   
sed -i "s/version =.*/version = \"${VERSION}\"/g" pyproject.toml    
sed -i "s/Version:.*/Version: ${VERSION}/g" deb_build/DEBIAN/control 
sed -i '' "s/'CFBundleShortVersionString': '.*'/'CFBundleShortVersionString': '${VERSION}'/g" eyeblink_gui.spec
sed -i '' "s/version='3.0.0'/version='${VERSION}'/g" eyeblink_gui.spec

git add setup.py pyproject.toml deb_build/DEBIAN/control 
git commit -m "feat(versions): update setup.py, pyproject.toml and deb_build/DEBIAN/control to ${VERSION}"

# now finish hotfix (e.g.  git flow hotfix finish 2.0.2 and push the develop/main and push tags)  

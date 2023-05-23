#!/usr/bin/env bash
set -Eeuxo pipefail

# The person performing the release would do the following:

# 1. Clone or pip install https://github.com/scoville/github-release-tool and put release.py into their path
# 2. Ensure they have created and checkout out a branch called "release/${version}" (i.e. a staging branch) with the code for the next srelease
# 3. ./releaser.sh ${version} will update setup.py with latest version and commit it, then perform the git flow operations needed to automate the release
# 4. The ci will build on that tag and deploy the Github release

VERSION=$1

if [ -z "$1" ]
  then
    echo "No argument supplied for required version"
    exit 1
fi

sed -i "s/version.*/version=\"${VERSION}\"\,/g" setup.py   
sed -i "s/version =.*/version = \"${VERSION}\"\,/g" pyproject.toml      
sed -i "s/Version:.*/Version: \"${VERSION}\"\,/g" deb_build/DEBIAN/control 

git add setup.py pyproject.toml deb_build/DEBIAN/control 
git commit -m "feat(versions): upate setup.py, pyproject.toml and deb_build/DEBIAN/control to ${VERSION}"
git push 

release.py --release_branch release/${VERSION} --production_branch main


#!/usr/bin/env bash
set -Eeuxo pipefail
# ensure you are on branch: hotfix/2.0.2  (e.g.  git flow hotfix start 2.0.2)

VERSION=$1

if [ -z "$1" ]
  then
    echo "No argument supplied for required version"
    exit 1
fi

./update_version_strings.sh ${VERSION}

git add setup.py pyproject.toml deb_build/DEBIAN/control
git commit -m "feat(versions): update setup.py, pyproject.toml and deb_build/DEBIAN/control to ${VERSION}"

# now finish hotfix (e.g.  git flow hotfix finish 2.0.2 and push the develop/main and push tags)  

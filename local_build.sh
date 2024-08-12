#!/bin/bash
# Provide release version as first argument to this script

binary_name=dryeye_defender
deb_name=dryeye_defender
app_name='DryEye Defender'
python_version='3.11'

RELEASE_VERSION=$1

RELEASE_VERSION=${RELEASE_VERSION} cxfreeze build

mkdir -p deb_build/opt/${binary_name}
cp -R "build/exe.linux-x86_64-${python_version}/." deb_build/opt/${binary_name}/

find deb_build/opt/${binary_name} -type f -exec chmod 644 -- {} +
find deb_build/opt/${binary_name} -type d -exec chmod 755 -- {} +

chmod +x deb_build/opt/${binary_name}/${binary_name}
#dpkg-deb --build --root-owner-group deb_build ${deb_name}_${RELEASE_VERSION}_all.deb

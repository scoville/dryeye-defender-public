# DryEye Defender

The graphical user interface for the DryEye Defender software: detecting blinks and providing reminders to blink.

## Repos

- [This repo](https://github.com/scoville/dryeye-defender)
  - [Submodule: Backend repo](https://github.com/scoville/blink-detection)
    - [Submodule of Submodule: Evaluation repo](https://github.com/scoville/blink-detection-evaluation)

## How to install

### Local

1. Create a venv of python3.8
    1. `python3.8 -m venv .venv`
    2. `source .venv/bin/activate`

2. Update submodules
   1. `git submodule update --init`

3. Install `requirement.txt`
    1. `python -m pip install -r requirements.txt` (or `requirements_mac.txt` / `requirements_windows.txt` if on Mac or Windows)
    1. for linting and ci libraries : `python -m pip install -r requirements_ci.txt`

4. Install other repo with pip
    1. `python -m pip install submodules/blink-detection`
    2. or using another solution `python -m pip install "git+https://github.com/scoville/blink-detection.git"`

5. Run program
   1. `python -m dryeye_defender`

### Docker

- For the webcam, the docker-compose mounts a few video sockets in the hope of capturing the correct one for your machine, you may need to edit docker-compose if your webcam is not one of these devices.
- We mount the current repo so edits to code will be reflected live in the container.

#### Quickstart

`git submodule update --init && docker-compose up`
Will launch the GUI, performing all the below operations, and update submodule

To run the tests:
`git submodule update --init && docker-compose run --entrypoint pytest dryeye_defender_service`

#### Step-by-step

1. Building docker image
   1. `docker compose build`
   1. or `docker-compose build`

2. Running docker container
   1. `docker compose up`

3. Run program
   1. `python -m dryeye_defender`

### Export program

#### Binary

from the venv created before

1. `pip install -e submodules/blink-detection/` Only locally (not needed for docker)
2. `python setup.py build`
3. `build/exe.linux-x86_64-3.8/eyehealth` to run the binary file

#### Deb file

1. `mkdir -p deb_build/opt/eyehealth`
2. we copy the files from the build folder to the deb package folder before deb creation
   1. `cp -R build/exe.linux-x86_64-3.8/* deb_build/opt/eyehealth`
3. we change the permissions of the files and folders because files will keep permissions after packaging
   1. `find deb_build/opt/eyehealth -type f -exec chmod 644 -- {} +`
   2. `find deb_build/opt/eyehealth -type d -exec chmod 755 -- {} +`
   3. `find deb_build/usr/share -type f -exec chmod 644 -- {} +`
4. we make the binary and desktop file executable
   1. `chmod +x deb_build/opt/eyehealth/eyehealth`
   2. `chmod +x deb_build/usr/share/applications/eyehealth.desktop`
5. build the deb package with the official tool
   1. `dpkg-deb --build --root-owner-group deb_build`
6. `sudo apt install ./deb_build.deb` Only work locally not on docker

#### Signing the app for mac os

> Currently, the app works without signing. The reason it was not working before is that cxfreeze was breaking the build with bad mandatory signing, but with pyinstaller the problem is not present and you can still try the app without signing. If we want the user to not have a lot of warning at launch, we will need to sign the app.

https://app.clickup.com/t/7508642/POC-2780

To manually add signing:

- Add a signing certificate on mac os keychain
- If it's a dev certificate we need to add this certificate also to trust our certificate <https://developer.apple.com/forums/thread/662300>
- On the certificate, get more info to see what is the `common name` of the certificate
  - e.g `Mac Developer: Benjamin Lowe (FDFD2FE)`
- use this command to sign the app :
  - `codesign --deep --force --verify --verbose --sign "Mac Developer: Benjamin Lowe (NKNH9AYUS2)" /full/path/to/the/app/DryEye_Defender.app`
- verify the signing
  - `codesign -dv --verbose=4 /Users/felix/Documents/poc/blink-detection-gui/dist/DryEye_Defender.app`

## What is a breaking change for this repo?

- For simplicity, for time being (as we don't have pip dependency resolution), we'd basically release a new release of GUI with every backend release after testing compatibility. Once we have a private pip package for the backend, we can do more complex version dependency, e.g. allowing us to make this repo dependent on all backwards compatible versions of the backend, such that a breaking change is only when there is a changed interaction with the backend (e.g. requiring a new attribute from the backend)  

## Querying DB
```
SELECT strftime('%Y-%m-%d %H:%M:%S', blink_time, 'unixepoch') AS minute_utc, * from blink_history ORDER BY blink_time DESC;


SELECT strftime('%Y-%m-%d %H:%M', blink_time, 'unixepoch') AS minute_utc,
       COUNT(*) AS events_per_minute
FROM blink_history
WHERE blink_marker = 1 AND blink_time >= strftime('%s', 'now') - (600 * 60)
GROUP BY minute_utc;

```

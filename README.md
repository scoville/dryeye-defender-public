# Eye blink detection gui

Basic prototype for detecting eyeblink and warn user when blinking is too low

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
    1. `python -m pip install submodules/eyeblink-detection`
    2. or using another solution `python -m pip install "git+https://github.com/scoville/eyeblink-detection.git"`

5. Run program
   1. `python -m eyeblink_gui`

### Docker

- For the webcam, the docker-compose mounts a few video sockets in the hope of capturing the correct one for your machine, you may need to edit docker-compose if your webcam is not one of these devices.
- We mount the current repo so edits to code will be reflected live in the container.

#### Quickstart

`git submodule update --init && docker-compose up` 
Will launch the GUI, performing all the below operations, and update submodule

#### Step-by-step

1. Building docker image
   1. `docker compose build`
   1. or `docker-compose build`

2. Running docker image
   1. `docker compose run --rm eyeblink bash`
   1. or `docker-compose run --rm eyeblink bash`

3. Build latest model:

```
cd submodules/eyeblink-detection/ && \
python scripts/optimizer/export_to_openvino.py && \
cd ../../
```

4. Run program
   1. `python -m eyeblink_gui`

### Export program

#### Binary

from the venv create before

1. `pip install -e submodules/eyeblink-detection/` Only locally (not needed for docker)
2. `python setup.py build`
3. `build/exe.linux-x86_64-3.8/eyehealth` to run the binary file

#### Deb file

1. mkdir -p deb_build/opt/eyehealth
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

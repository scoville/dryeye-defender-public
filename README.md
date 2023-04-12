# Eye blink detection gui

Basic prototype for detecting eyeblink and warn user when blinking is too low

## How to install

### Local
1. Create a venv of python3.8
    1. `python3.8 -m venv .venv`
    2. `source .venv/bin/activate`

2. Update submodules
   1.  `git submodule update --init` 

3. Install `requirement.txt`
    1. `python -m pip install -r requirements.txt`
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

`docker-compose up` will launch the GUI, performing all the below operations

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

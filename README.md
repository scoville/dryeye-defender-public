# Eye blink detection gui

Basic prototype for detecting eyeblink and warn user when blinking is too low

## How to install
1. Create a venv of python3.8
    1. `python -m venv .venv`
    2. `source .venv/bin/activate`

2. Install `requirement.txt`
    1. `python -m pip install -r requirements.txt`

3. Install other repo with pip
    1. `python -m pip install submodules/eyeblink-detection`
    2. or using another solution `python -m pip install "git+https://github.com/scoville/eyeblink-detection.git"`

<!-- 4. Copy checkpoint file from eyeblink-detection repo
   1. `mkdir -p ./assets/ckpt`
   2. `cp ../eyeblink-detection/assets/ckpt/epoch_80.pth.tar ./assets/ckpt/epoch_80.pth.tar ` -->
5. Run program
   1. `python -m eyeblink-gui`
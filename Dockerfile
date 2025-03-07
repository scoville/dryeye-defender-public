FROM python:3.11

ARG USER_ID=1000
ARG GROUP_ID=1000
ARG AUX_GROUP_IDS=""
ARG USERNAME=user

# ENV QT_DEBUG_PLUGINS=1

# Add non-root user and give permissions to workdir:
RUN groupadd --gid "${GROUP_ID}" "${USERNAME}" && \
    useradd -m --uid "${USER_ID}" --gid "${GROUP_ID}" "${USERNAME}" && \
    echo "${AUX_GROUP_IDS}" | xargs -n1 echo | xargs -I% groupadd --gid % group% && \
    echo "${AUX_GROUP_IDS}" | xargs -n1 echo | xargs -I% usermod --append --groups group% "${USERNAME}"

RUN apt-get update && apt-get autoclean && \
    apt-get install -y --no-install-recommends \
    libegl1-mesa \
    libgl1 \
    libdbus-1-3 \
    libxcb1\
    libxcb-icccm4\
    libxcb-image0\
    libxcb-keysyms1\
    libxcb-randr0\
    libxcb-render-util0\
    x11-xserver-utils \
    libxkbcommon-x11-0 \
    x11-utils \
    libxcb-cursor-dev \
    libgirepository1.0-dev \
    gcc \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    gir1.2-gtk-4.0


# Install xvfb
# Running this separately as running it as part of the command above causes an exit code 100
RUN apt-get update && apt-get install -y --no-install-recommends xvfb && apt-get clean

# Install packages, including CI requirements to overwrite poor package management by other libraries
COPY requirements.txt .
COPY requirements_ci.txt .
COPY requirements_linux.txt .
COPY submodules/blink-detection/requirements.txt submodules/blink-detection/requirements.txt

RUN pip install -r requirements_ci.txt

# Make the git submodule accessible:
ENV PYTHONPATH="submodules/blink-detection:$PYTHONPATH"

USER user

# Not needed, but makes it easy to run outside of Jenkins:
WORKDIR /home/user/dryeye_defender
# COPY . .

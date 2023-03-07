FROM python:3.8

ARG USER_ID=1001
ARG GROUP_ID=1001
ARG AUX_GROUP_IDS=""
ARG USERNAME=user

# Add non-root user and give permissions to workdir:
RUN groupadd --gid "${GROUP_ID}" "${USERNAME}" && \
    useradd -m --uid "${USER_ID}" --gid "${GROUP_ID}" "${USERNAME}" && \
    echo "${AUX_GROUP_IDS}" | xargs -n1 echo | xargs -I% groupadd --gid % group% && \
    echo "${AUX_GROUP_IDS}" | xargs -n1 echo | xargs -I% usermod --append --groups group% "${USERNAME}"

WORKDIR /home/app

COPY requirements.txt ./

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

USER user
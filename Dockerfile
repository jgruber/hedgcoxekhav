FROM ubuntu:latest
LABEL maintainer="John Gruber <john.t.gruber@gmail.com>"

WORKDIR /

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    python3-pip \
    git

RUN cd /var/lib && \
    git clone https://github.com/jgruber/hedgcoxekhav.git && \
    cd /var/lib/hedgcoxekhav && \
    pip3 install -r requirements.txt && \
    chmod +x /var/lib/hedgcoxekhav/avswitcher.py

ENV USER 'root'

ENTRYPOINT [ "/var/lib/hedgcoxekhav/avswitcher.py" ]

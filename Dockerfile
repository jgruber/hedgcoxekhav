FROM ubuntu:20.04
LABEL maintainer="John Gruber <john.t.gruber@gmail.com>"

WORKDIR /

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    python3-pip \
    unzip \
    git

RUN cd /var/lib && \
    git clone https://github.com/jgruber/hedgcoxekhav.git && \
    cd /var/lib/hedgcoxekhav && \
    pip3 install -r requirements.txt && \
    chmod +x /var/lib/hedgcoxekhav/avswitcher.py

COPY bin/XAir_Ubuntu.zip /var/lib/hedgcoxekhav/XAir_Ubuntu.zip

RUN cd /var/lib/hedgcoxekhav/bin && \
    unzip XAir_Ubuntu.zip && \
    mv XAir_Command /usr/bin/XAir_Command && \
    chmod +x /usr/bin/XAir_Command && \
    mv XAirGetScene /usr/bin/XAirGetScene && \
    chmod +x /usr/bin/XAirGetScene && \
    mv XAriSetScene /usr/bin/XAriSetScene && \
    chmod +X /usr/bin/XAriSetScene

VOLUME [ "/static" ]

ENV USER 'root'

ENTRYPOINT [ "/var/lib/hedgcoxekhav/avswitcher.py" ]

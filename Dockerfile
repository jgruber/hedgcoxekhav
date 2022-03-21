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
    chmod +x /var/lib/hedgcoxekhav/avswitcher.py && \
    cd /var/lib/hedgcoxekhav/bin && \
    unzip XAir_amd64.zip && \
    mv XAir_Command /usr/bin/XAir_Command && \
    chmod +x /usr/bin/XAir_Command && \
    mv XAirGetScene /usr/bin/XAirGetScene && \
    chmod +x /usr/bin/XAirGetScene && \
    mv XAirSetScene /usr/bin/XAriSetScene && \
    chmod +x /usr/bin/XAriSetScene

VOLUME [ "/static" ]

ENV USER 'root'

ENTRYPOINT [ "/var/lib/hedgcoxekhav/avswitcher.py" ]

FROM --platform=arm64 python:3.8

# wget installation
RUN apt-get update \
    && apt-get install -y wget \
    && rm -rf /var/lib/apt/lists/*

# texlive installation
COPY texlive.profile /
RUN wget https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
RUN tar -xvf install-tl-unx.tar.gz
RUN rm install-tl-unx.tar.gz
RUN find . -maxdepth 1 -type d -name "install-tl-*" -exec {}/install-tl -profile texlive.profile \;

ENV PATH="/usr/local/texlive/2021/bin/aarch64-linux:$PATH"

FROM --platform=arm64 python:3.8

# nodejs, pdf2svg and ghostscript (ps2pdf) installation
RUN curl -fsSL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get update \
    && apt-get install -y nodejs wget pdf2svg ghostscript \
    && rm -rf /var/lib/apt/lists/*

# svgo installation
RUN npm -g install svgo

# texlive installation
COPY texlive.profile /
RUN wget https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
RUN tar -xvf install-tl-unx.tar.gz
RUN rm install-tl-unx.tar.gz
RUN find . -maxdepth 1 -type d -name "install-tl-*" -exec {}/install-tl -profile texlive.profile \;

ENV PATH="/usr/local/texlive/2021/bin/aarch64-linux:$PATH"


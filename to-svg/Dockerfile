FROM --platform=arm64 python:3.8 as build-stage
COPY requirements.txt /
RUN pip install -r requirements.txt

FROM antoinesion/python-texlive

WORKDIR /function
COPY . /function/

# nodejs, pdf2svg and ghostscript (ps2pdf) installation
RUN curl -fsSL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get update \
    && apt-get install -y nodejs pdf2svg ghostscript \
    && rm -rf /var/lib/apt/lists/*

# svgo installation
RUN npm -g install svgo

# copy pip packages
COPY --from=build-stage /usr/local/lib/python3.8/site-packages/ /usr/local/lib/python3.8/site-packages/
COPY --from=build-stage /usr/local/bin/fdk /usr/local/bin/

ENTRYPOINT ["fdk", "func.py", "handler"]

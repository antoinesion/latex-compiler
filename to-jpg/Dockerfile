FROM --platform=arm64 python:3.8 as build-stage

# install PyMuPDF build dependency: gcc
RUN apt-get update \
    && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /
RUN pip install -r requirements.txt

FROM antoinesion/python-texlive

WORKDIR /function
COPY . /function/

# copy pip packages
COPY --from=build-stage /usr/local/lib/python3.8/site-packages/ /usr/local/lib/python3.8/site-packages/
COPY --from=build-stage /usr/local/bin/fdk /usr/local/bin/

ENTRYPOINT ["fdk", "func.py", "handler"]

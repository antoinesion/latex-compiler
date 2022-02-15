FROM --platform=amd64 python:3.8 as build-stage
COPY requirements.txt /
RUN pip install -r requirements.txt

FROM latex-compiler-base

WORKDIR /function
COPY . /function/

# copy pip packages
COPY --from=build-stage /usr/local/lib/python3.8/site-packages/ /usr/local/lib/python3.8/site-packages/
COPY --from=build-stage /usr/local/bin/fdk /usr/local/bin/

ENTRYPOINT ["fdk", "func.py", "handler"]

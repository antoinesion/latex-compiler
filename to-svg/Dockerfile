FROM antoinesion/python-nodejs-texlive-svg as build-stage
WORKDIR /function
COPY requirements.txt /function/
RUN pip install -r requirements.txt

FROM antoinesion/python-nodejs-texlive-svg
WORKDIR /function
COPY . /function/
COPY --from=build-stage /usr/local/lib/python3.8/site-packages/ /usr/local/lib/python3.8/site-packages/
COPY --from=build-stage /usr/local/bin/fdk /usr/local/bin/
ENTRYPOINT ["fdk", "func.py", "handler"]

import io
import os
import json
import logging
import re
import sys
from subprocess import call
import time
from tempfile import mkstemp
from urllib.request import urlretrieve

from fdk import response

COMPILATION_DIR = "/tmp"
LATEX_HEADER = """\\batchmode
\\documentclass[preview,border=1mm,convert={outext=.svg,command=\\unexpanded{pdf2svg \\infile\\space\\outfile}},multi=false]{standalone}

"""
POSTGRESQL_MAX_FIELD_SIZE = 1e9


def handler(ctx, data: io.BytesIO = None):
    job_start = time.time()
    logging.getLogger().info("Starting job...")
    try:
        try:
            body = json.loads(data.getvalue())
        except ValueError:
            logging.getLogger().error("Error: payload is missing.")
            return response.Response(
                ctx, response_data=json.dumps(
                    {
                        "message": "payload is missing",
                        "code": "payload_missing"
                    }),
                headers={"Content-Type": "application/json"},
                status_code=400)

        if not "latex" in body:
            logging.getLogger().error("Error: payload is missing")
            return response.Response(
                ctx, response_data=json.dumps(
                    {
                        "message": "'latex' field is missing in payload",
                        "code": "latex_missing"
                    }),
                headers={"Content-Type": "application/json"},
                status_code=400)

        latex = body.get("latex")
        images = body.get("images", {})

        logging.getLogger().info("Preparing latex file...")
        os.chdir(COMPILATION_DIR)
        input_file, input_file_path = mkstemp(dir=COMPILATION_DIR)
        input_filename = os.path.split(input_file_path)[1]
        os.write(input_file, (LATEX_HEADER + latex).encode('utf-8'))
        os.close(input_file)

        if len(images):
            logging.getLogger().info("Retrieving images...")
        for (image_filename, image_url) in images.items():
            try:
                urlretrieve(image_url, image_filename)
            except Exception as e:
                logging.getLogger().error(
                    f"Error: unable to retrieve image '{image_filename}' at url '{image_url}'.")
                return response.Response(
                    ctx, response_data=json.dumps(
                        {
                            "message": f"unable to retrieve image '{image_filename}' at url '{image_url}'",
                            "image_filename": image_filename,
                            "image_url": image_url,
                            "code": "image_error"
                        }),
                    headers={"Content-Type": "application/json"},
                    status_code=400)

        logging.getLogger().info("Compiling latex...")
        call(['pdflatex', '-shell-escape', input_filename])
        output_filename = input_filename + '.svg'
        try:
            with open(output_filename, "r") as f:
                pass
        except:
            logging.getLogger().error("Error: compilation failed.")
            return response.Response(
                ctx, response_data=json.dumps(
                    {
                        "message": "compilation failed",
                        "code": "latex_error"
                    }),
                headers={"Content-Type": "application/json"},
                status_code=400)

        logging.getLogger().info("Optimizing svg...")
        optimized_filename = input_filename + '.min.svg'
        call(["svgo", "--config", "/function/svgo.config.js",
             output_filename, "-o", optimized_filename])
        with open(optimized_filename, 'r') as f:
            svg = f.read()
        svg = svg.replace("stroke:#000;", "")
        svg = svg.replace("fill:#000;", "")
        width_attr = re.search(r'width="[0-9.]*(pt)?"\s', svg)
        svg = svg[:width_attr.start()] + svg[width_attr.end():]
        height_attr = re.search(r'height="[0-9.]*(pt)?"\s', svg)
        svg = svg[:height_attr.start()] + svg[height_attr.end():]
        viewBox_width_attr_start = re.search(r'viewBox="0 0 ', svg)
        viewBox_width_attr_end = re.search(r'viewBox="0 0 [0-9.]*', svg)
        svg = svg[:viewBox_width_attr_start.end()] + "355.05" + \
            svg[viewBox_width_attr_end.end():]
        if sys.getsizeof(svg) > POSTGRESQL_MAX_FIELD_SIZE:
            logging.getLogger().error("Error: svg size exceeds PostgreSQL limitations")
            return response.Response(
                ctx, response_data=json.dumps(
                    {
                        "message": "svg size exceeds PostgreSQL limitations",
                        "svg_size": sys.getsizeof(svg),
                        "code": "svg_size_error"
                    }),
                headers={"Content-Type": "application/json"},
                status_code=400)
    except Exception as e:
        logging.getLogger().critical(f"Unknown error: {e}")
        return response.Response(
            ctx, response_data=json.dumps({
                "message": "unknown error",
                "code": "unknown_error"
            }),
            headers={"Content-Type": "application/json"}
        )

    job_duration_in_second = round(time.time() - job_start, 2)
    logging.getLogger().info(f"Job done in {job_duration_in_second}s!")
    return response.Response(
        ctx, response_data=json.dumps({
            "message": "compilation succeeded",
            "svg": svg
        }),
        headers={"Content-Type": "application/json"}
    )

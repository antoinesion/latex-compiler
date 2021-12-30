import io
import os
import json
import re
from http.client import OK, BAD_REQUEST, INTERNAL_SERVER_ERROR
from subprocess import call
from tempfile import mkstemp
from email import parser

from fdk import response

COMPILATION_DIR = "/tmp"
LATEX_HEADER = """\\batchmode
\\documentclass[preview,border=1mm,convert={outext=.svg,command=\\unexpanded{pdf2svg \\infile\\space\\outfile}},multi=false]{standalone}

"""


def handler(ctx, data: io.BytesIO = None):
    try:
        formdata = parser.BytesParser().parsebytes(data.read())
        print(formdata.get_payload())
        try:
            body = json.loads(data.getvalue())
        except ValueError:
            return response.Response(
                ctx, response_data=json.dumps(
                    {
                        "message": "payload is missing",
                        "code": "payload_missing"
                    }),
                headers={"Content-Type": "application/json"},
                status_code=BAD_REQUEST)

        if not "latex" in body:
            return response.Response(
                ctx, response_data=json.dumps(
                    {
                        "message": "'latex' field is missing in payload",
                        "code": "latex_missing"
                    }),
                headers={"Content-Type": "application/json"},
                status_code=BAD_REQUEST)

        latex = body.get("latex")
        images = body.get("images", {})

        os.chdir(COMPILATION_DIR)
        input_file, input_file_path = mkstemp(dir=COMPILATION_DIR)
        input_filename = os.path.split(input_file_path)[1]
        os.write(input_file, (LATEX_HEADER + latex).encode('utf-8'))
        os.close(input_file)

        for (image_filename, image_file) in images.items():
            with open(image_filename, 'wb') as f:
                f.write(image_file.read())

        call(['pdflatex', '-shell-escape', input_filename])
        output_filename = input_filename + '.svg'
        try:
            with open(output_filename, "r") as f:
                pass
        except:
            return response.Response(
                ctx, response_data=json.dumps(
                    {
                        "message": "compilation failed",
                        "code": "latex_error"
                    }),
                headers={"Content-Type": "application/json"},
                status_code=BAD_REQUEST)

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
    except Exception as e:
        return response.Response(
            ctx, response_data=json.dumps({
                "message": "unknown error",
                "code": "unknown_error",
                "error": str(e)
            }),
            headers={"Content-Type": "application/json"},
            status_code=INTERNAL_SERVER_ERROR
        )

    return response.Response(
        ctx, response_data=json.dumps({
            "message": "compilation succeeded",
            "code": "success",
            "svg": svg
        }),
        headers={"Content-Type": "application/json"},
        status_code=OK
    )

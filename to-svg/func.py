import io
import os
import re
from http.client import OK, BAD_REQUEST, INTERNAL_SERVER_ERROR
from subprocess import call
from tempfile import mkstemp
from requests_toolbelt import MultipartDecoder, MultipartEncoder

from fdk import response

COMPILATION_DIR = "/tmp"
LATEX_HEADER = b"""\\batchmode
\\RequirePackage{fix-cm}
\\documentclass[preview,border=1mm,varwidth=500pt,convert={outext=.svg,command=\\unexpanded{pdf2svg \\infile\\space\\outfile}},multi=false]{standalone}

"""


def handler(ctx, data: io.BytesIO = None):
    os.chdir(COMPILATION_DIR)
    latex = None

    try:
        try:
            decoder = MultipartDecoder(
                data.read(), ctx.Headers()["content-type"])
            for field in decoder.parts:
                field_name = field.headers[b"Content-Disposition"].decode().split(";")[
                    1].split("=")[1][1:-1]
                if field_name == "latex":
                    latex = field.content
                if field_name == "image[]":
                    filename = field.headers[b"Content-Disposition"].decode().split(";")[
                        2].split("=")[1][1:-1]
                    with open(filename, "wb") as f:
                        f.write(field.content)
        except Exception as e:
            encoder = MultipartEncoder({
                "message": "cannot parse form data",
                "code": "parsing_error",
                "error": str(e)
            })
            return response.Response(
                ctx, response_data=encoder.to_string(),
                headers={"Content-Type": encoder.content_type},
                status_code=BAD_REQUEST)

        if not latex:
            encoder = MultipartEncoder({
                "message": "'latex' field is missing in form data",
                "code": "latex_missing"
            })
            return response.Response(
                ctx, response_data=encoder.to_string(),
                headers={"Content-Type": encoder.content_type},
                status_code=BAD_REQUEST)

        input_file, input_file_path = mkstemp(dir=COMPILATION_DIR)
        input_filename = os.path.split(input_file_path)[1]
        os.write(input_file, LATEX_HEADER + latex)
        os.close(input_file)

        call(['pdflatex', '-shell-escape', input_filename])
        output_filename = input_filename + '.svg'
        try:
            with open(output_filename, "r") as f:
                pass
        except:
            encoder = MultipartEncoder({
                "message": "compilation failed",
                "code": "latex_error"
            })
            return response.Response(
                ctx, response_data=encoder.to_string(),
                headers={"Content-Type": encoder.content_type},
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
        svg = svg[:viewBox_width_attr_start.end()] + "504" + \
            svg[viewBox_width_attr_end.end():]

        with open('result.svg', 'w') as f:
            f.write(svg)

    except Exception as e:
        encoder = MultipartEncoder({
            "message": "unknown error",
            "code": "unknown_error",
            "error": str(e)
        })
        return response.Response(
            ctx, response_data=encoder.to_string(),
            headers={"Content-Type": encoder.content_type},
            status_code=INTERNAL_SERVER_ERROR
        )

    encoder = MultipartEncoder({
        "message": "compilation succeeded",
        "code": "success",
        "svg": ("result.svg", svg, "image/svg+xml")
    })
    return response.Response(
        ctx, response_data=encoder.to_string(),
        headers={"Content-Type": encoder.content_type},
        status_code=OK
    )

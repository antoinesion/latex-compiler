import io
import os
import re
import glob
from http.client import OK, BAD_REQUEST, INTERNAL_SERVER_ERROR
from subprocess import call
from tempfile import mkstemp
from requests_toolbelt import MultipartDecoder, MultipartEncoder
import sentry_sdk
import logging

from fdk import response

sentry_sdk.init(
    "https://abb12a4b6cf84dd792da1caf55016e87@o1109165.ingest.sentry.io/6194998",
    traces_sample_rate=1.0
)

COMPILATION_DIR = "/tmp"
LATEX_TEMPLATE = b"""\\batchmode
\\RequirePackage{fix-cm}
\\documentclass[preview,border=%(padding).1fpt,convert={outext=.svg,command=\\unexpanded{pdf2svg \\infile\\space\\outfile}},multi=false]{standalone}

%(packages)s
\\usepackage[paperwidth=%(width).1fpt, margin=0]{geometry}

\\begin{document}
\\fontsize{%(font_size).1fpt}{%(baseline_skip).1fpt}\selectfont

%(latex)s

\\end{document}
"""


def handler(ctx, data: io.BytesIO = None):
    with sentry_sdk.start_transaction(op="task", name="to-svg"):
        logger = logging.getLogger()
        logger.log(logging.INFO, "running")

        os.chdir(COMPILATION_DIR)

        width = 595  # A4 width
        padding = 3
        font_size = 10
        baseline_skip = 1.2
        packages = ''
        latex = None

        try:
            try:
                decoder = MultipartDecoder(
                    data.read(), ctx.Headers()["content-type"])
                for field in decoder.parts:
                    field_name = field.headers[b"Content-Disposition"].decode().split(";")[
                        1].split("=")[1][1:-1]
                    if field_name == "width":
                        width = float(field.content)
                    if field_name == "padding":
                        padding = float(field.content)
                    if field_name == "font_size":
                        font_size = float(field.content)
                    if field_name == "baseline_skip":
                        baseline_skip = float(field.content)
                    if field_name == "packages":
                        packages = field.content
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

            if latex == None:
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

            os.write(input_file, LATEX_TEMPLATE % {
                b'width': width,
                b'padding': padding,
                b'font_size': font_size,
                b'baseline_skip': font_size * baseline_skip,
                b'packages': packages,
                b'latex': latex
            })
            os.close(input_file)

            call(['pdflatex', '-shell-escape', input_filename])
            output_filename = input_filename + '.svg'
            try:
                with open(output_filename, "r") as f:
                    pass
            except:
                for tmp_file in glob.glob(input_filename + '*'):
                    os.remove(tmp_file)

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
            svg = re.sub(r'width="[0-9.]*(pt)?"\s', '', svg, 1)
            svg = re.sub(r'height="[0-9.]*(pt)?"\s', '', svg, 1)
            view_box_width = re.search(
                r'viewBox="[0-9.]* [0-9.]* ([0-9.]*) [0-9.]*"', svg)
            svg_width = float(view_box_width.group(1))
            if svg_width / (width+padding*2) < 0.9:
                svg = svg[:view_box_width.start(
                    1)] + str(width+padding*2) + svg[view_box_width.end(1):]

            for tmp_file in glob.glob(input_filename + '*'):
                os.remove(tmp_file)

        except Exception as e:
            sentry_sdk.capture_exception(e)
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

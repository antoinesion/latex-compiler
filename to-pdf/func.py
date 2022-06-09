import io
import os
import glob
from http.client import OK, BAD_REQUEST, INTERNAL_SERVER_ERROR
from subprocess import call, TimeoutExpired
from tempfile import mkstemp
from typing import List, Optional
from requests_toolbelt import MultipartDecoder, MultipartEncoder
import sentry_sdk

from fdk.response import Response
from fdk.context import InvokeContext

sentry_sdk.init(
    "https://abb12a4b6cf84dd792da1caf55016e87@o1109165.ingest.sentry.io/6194998",
    traces_sample_rate=0.1
)

COMPILATION_DIR = "/tmp"
LATEX_TEMPLATE = b"""\\batchmode
\\RequirePackage{fix-cm}
%(document_class)s

%(packages)s

\\begin{document}
\\fontsize{%(font_size).1fpt}{%(baseline_skip).1fpt}\selectfont

%(latex)s

\\end{document}
"""

PX_TO_PT_FACTOR = 0.75


def px_to_pt(px: float) -> float:
    return round(px * PX_TO_PT_FACTOR, 2)


def clean_files(input_filename: Optional[str], images_filename: List[str] = []) -> None:
    if input_filename:
        for tmp_file in glob.glob(input_filename + '*'):
            os.remove(tmp_file)
    for image_filename in images_filename:
        os.remove(image_filename)


def handler(ctx: InvokeContext, data: io.BytesIO = None):
    with sentry_sdk.start_transaction(op="task", name="to-pdf"):
        os.chdir(COMPILATION_DIR)

        # values in pt
        document_class = b'\\documentclass{report}'
        double_compilation = False
        font_size = 10
        baseline_skip = 1.2
        packages = b''
        latex = None

        images_filename = []
        input_filename = None

        compilation_timeout = 10

        try:
            try:
                decoder = MultipartDecoder(
                    data.read(), ctx.Headers()["content-type"])
                for field in decoder.parts:
                    field_name = field.headers[b"Content-Disposition"].decode().split(";")[
                        1].split("=")[1][1:-1]
                    if field_name == "document_class":
                        document_class = field.content
                    if field_name == "double_compilation":
                        double_compilation = field.content.decode() == "True"
                    if field_name == "font_size":
                        font_size = px_to_pt(float(field.content))
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
                        images_filename.append(filename)
                    if field_name == "compilation_timeout":
                        compilation_timeout = min(float(field.content), 20)
            except Exception as e:
                clean_files(input_filename=input_filename,
                            images_filename=images_filename)
                encoder = MultipartEncoder({
                    "message": "cannot parse form data",
                    "code": "parsing_error",
                    "error": str(e)
                })
                return Response(
                    ctx, response_data=encoder.to_string(),
                    headers={"Content-Type": encoder.content_type},
                    status_code=BAD_REQUEST)

            if latex == None:
                encoder = MultipartEncoder({
                    "message": "'latex' field is missing in form data",
                    "code": "latex_missing"
                })
                return Response(
                    ctx, response_data=encoder.to_string(),
                    headers={"Content-Type": encoder.content_type},
                    status_code=BAD_REQUEST)

            input_file, input_file_path = mkstemp(dir=COMPILATION_DIR)
            input_filename = os.path.split(input_file_path)[1]

            os.write(input_file, LATEX_TEMPLATE % {
                b'document_class': document_class,
                b'font_size': font_size,
                b'baseline_skip': font_size * baseline_skip,
                b'packages': packages,
                b'latex': latex
            })
            os.close(input_file)

            try:
                call(['pdflatex', '-shell-escape', input_filename],
                     timeout=compilation_timeout)
            except TimeoutExpired:
                clean_files(input_filename=input_filename,
                            images_filename=images_filename)
                encoder = MultipartEncoder({
                    "message": "compilation timeout",
                    "code": "timeout_error"
                })
                return Response(
                    ctx, response_data=encoder.to_string(),
                    headers={"Content-Type": encoder.content_type},
                    status_code=BAD_REQUEST)

            if double_compilation:
                call(['pdflatex', '-shell-escape', input_filename])

            output_filename = input_filename + '.pdf'

            try:
                with open(output_filename, "rb") as f:
                    blob = io.BytesIO(f.read())
            except:
                clean_files(input_filename=input_filename,
                            images_filename=images_filename)
                encoder = MultipartEncoder({
                    "message": "compilation failed",
                    "code": "latex_error"
                })
                return Response(
                    ctx, response_data=encoder.to_string(),
                    headers={"Content-Type": encoder.content_type},
                    status_code=BAD_REQUEST)

        except Exception as e:
            clean_files(input_filename=input_filename,
                        images_filename=images_filename)
            sentry_sdk.capture_exception(e)
            encoder = MultipartEncoder({
                "message": "unknown error",
                "code": "unknown_error",
                "error": str(e)
            })
            return Response(
                ctx, response_data=encoder.to_string(),
                headers={"Content-Type": encoder.content_type},
                status_code=INTERNAL_SERVER_ERROR
            )

        clean_files(input_filename=input_filename,
                    images_filename=images_filename)
        encoder = MultipartEncoder({
            "message": "compilation succeeded",
            "code": "success",
            "pdf": ("result.pdf", blob)
        })
        return Response(
            ctx, response_data=encoder.to_string(),
            headers={"Content-Type": encoder.content_type},
            status_code=OK
        )

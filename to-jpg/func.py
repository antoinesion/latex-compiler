from fcntl import F_SEAL_SEAL
import io
import os
import glob
from http.client import OK, BAD_REQUEST, INTERNAL_SERVER_ERROR
from subprocess import call
from tempfile import mkstemp
import fitz
from PIL import Image
from requests_toolbelt import MultipartDecoder, MultipartEncoder
import sentry_sdk

from fdk import response

sentry_sdk.init(
    "https://abb12a4b6cf84dd792da1caf55016e87@o1109165.ingest.sentry.io/6194998",
    traces_sample_rate=0.1
)

COMPILATION_DIR = "/tmp"
WIDTH_CONSTRAIN = b"\\usepackage[paperwidth=%(width).1fpt, margin=0pt]{geometry}"
LATEX_TEMPLATE = b"""\\batchmode
\\RequirePackage{fix-cm}
\\documentclass[preview,border={%(padding_left).1fpt %(padding_bottom).1fpt %(padding_right).1fpt %(padding_top).1fpt},varwidth=%(varwidth)s,multi=false]{standalone}

%(packages)s
%(width_constrain)s

\\begin{document}
\\fontsize{%(font_size).1fpt}{%(baseline_skip).1fpt}\selectfont

%(latex)s

\\end{document}
"""

PX_TO_PT_FACTOR = 0.75


def px_to_pt(px: float) -> float:
    return round(px * PX_TO_PT_FACTOR, 2)


def handler(ctx, data: io.BytesIO = None):
    with sentry_sdk.start_transaction(op="task", name="to-jpg"):
        os.chdir(COMPILATION_DIR)

        width = None

        # values in pt
        padding_left = 3
        padding_bottom = 3
        padding_right = 3
        padding_top = 3
        font_size = 10

        baseline_skip = 1.2
        packages = b''
        latex = None
        resolution = 5

        try:
            try:
                decoder = MultipartDecoder(
                    data.read(), ctx.Headers()["content-type"])
                for field in decoder.parts:
                    field_name = field.headers[b"Content-Disposition"].decode().split(";")[
                        1].split("=")[1][1:-1]
                    if field_name == "width":
                        if field.content == b'a4':
                            width = 595
                        else:
                            width = px_to_pt(float(field.content))
                    if field_name == "padding":
                        padding_left = padding_bottom = padding_right = padding_top = px_to_pt(
                            float(field.content))
                    if field_name == "padding_left":
                        padding_left = px_to_pt(float(field.content))
                    if field_name == "padding_bottom":
                        padding_bottom = px_to_pt(float(field.content))
                    if field_name == "padding_right":
                        padding_right = px_to_pt(float(field.content))
                    if field_name == "padding_top":
                        padding_top = px_to_pt(float(field.content))
                    if field_name == "font_size":
                        font_size = px_to_pt(float(field.content))
                    if field_name == "baseline_skip":
                        baseline_skip = float(field.content)
                    if field_name == "packages":
                        packages = field.content
                    if field_name == "latex":
                        latex = field.content
                    if field_name == "resolution":
                        resolution = int(field.content)
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

            if not width is None:
                width_constrain = WIDTH_CONSTRAIN % {b'width': width}
                varwidth = b'false'
            else:
                width_constrain = b''
                varwidth = b'595pt'

            os.write(input_file, LATEX_TEMPLATE % {
                b'width_constrain': width_constrain,
                b'varwidth': varwidth,
                b'padding_left': padding_left,
                b'padding_bottom': padding_bottom,
                b'padding_right': padding_right,
                b'padding_top': padding_top,
                b'font_size': font_size,
                b'baseline_skip': font_size * baseline_skip,
                b'packages': packages,
                b'latex': latex
            })
            os.close(input_file)

            call(['pdflatex', '-shell-escape', input_filename])
            output_filename = input_filename + '.pdf'
            matrix = fitz.Matrix(resolution, resolution)

            try:
                doc = fitz.open(output_filename)
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

            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes(
                "RGB", [pix.width, pix.height], pix.samples)
            blob = io.BytesIO()
            img.save(blob, 'JPEG')

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
            "jpg": ("result.jpg", blob)
        })
        return response.Response(
            ctx, response_data=encoder.to_string(),
            headers={"Content-Type": encoder.content_type},
            status_code=OK
        )

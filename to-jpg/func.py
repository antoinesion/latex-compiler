import io
import os
from http.client import OK, BAD_REQUEST, INTERNAL_SERVER_ERROR
from subprocess import call
from tempfile import mkstemp
import fitz
from PIL import Image
from requests_toolbelt import MultipartDecoder, MultipartEncoder

from fdk import response

COMPILATION_DIR = "/tmp"
LATEX_HEADER = b"""\\batchmode
\\RequirePackage{fix-cm}
\\documentclass[preview,border=3mm,varwidth=500pt,multi=false]{standalone}

"""


def handler(ctx, data: io.BytesIO = None):
    os.chdir(COMPILATION_DIR)
    latex = None
    resolution = 5

    try:
        try:
            decoder = MultipartDecoder(
                data.read(), ctx.Headers()["content-type"])
            for field in decoder.parts:
                field_name = field.headers[b"Content-Disposition"].decode().split(";")[
                    1].split("=")[1][1:-1]
                if field_name == "latex":
                    latex = field.content
                if field_name == "resolution":
                    resolution = int(field.content.decode())
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
        output_filename = input_filename + '.pdf'
        matrix = fitz.Matrix(resolution, resolution)

        try:
            doc = fitz.open(output_filename)
        except:
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
        "jpg": ("result.jpg", blob)
    })
    return response.Response(
        ctx, response_data=encoder.to_string(),
        headers={"Content-Type": encoder.content_type},
        status_code=OK
    )

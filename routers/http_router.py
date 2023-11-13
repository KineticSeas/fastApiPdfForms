###########################################################################################################
# KineticForms API Engine
#
# Copyright (c) 2023 - Kinetic Seas Inc.
# by Edward Honour and Joseph Lehman.
#
# http_router.py - Main FastAPI Project File.
#
# Optional Routes for File Upload and Download Processing
###########################################################################################################
from fastapi import FastAPI, File, UploadFile, APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from starlette.responses import Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
from kineticpdf import KineticPdf
from kinetichttp import KineticHttp
import tempfile

http_router = APIRouter()


##################################################################################
# Download a file using a post endpoint.
#
# This endpoint allows a file to be downloaded using an API call from
# Angular.
# The parameter is expected to be a JSON string with 2 parameters:
# {
#    "file_id": 21312,
#    "output_name": "something.pdf"
# }
##################################################################################

@http_router.post("/download/")
def download(response: Response, file_path, output_name):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Content-Disposition"]=output_name
    response.headers["Expires"] = "0"
    return FileResponse(file_path, media_type='application/octet-stream', filename=output_name)


##################################################################################
# Download a large file from a post endpoint.
# 2 enpoints are provided for downloading files due to front end specific issues.
#
# This endpoint allows a large file to be downloaded using an API call from
# Angular. The /download/ endpoint has limitations on file size.
#
# The parameter is expected to be a JSON string with 2 parameters:
# {
#    "file_id": 21312,
#    "output_name": "something.pdf"
# }
##################################################################################
@http_router.get("/large_download/")
def download_file(response: Response):
    file_path = "/euc-hockey-form-new2.pdf"  # Replace with the path to your file

    def file_generator(filename):
        with open(filename, "rb") as f:
            while True:
                chunk = f.read(8192)  # reading in 8K chunks
                if not chunk:
                    break
                yield chunk

    headers = {"Content-Type": "application/octet-stream", 'Content-Disposition':
               'attachment; filename="yourfilename.pdf"'}

    return StreamingResponse(file_generator(file_path), headers=headers)

#################################################################################
# Upload a blank PDF template for an organization.
# The properties (metadata) will be modified to add "form_id=somenumber" and
# "user_id=somenumber" value to the metadata keywords of the PDF. The is
# necessary to track forms that are
# uploaded by your users.  Make sure you get an updated file if you are
# distributing the PDF yourself.
#
# The parameters are the File being uploaded and a JSON string with the
# following fields at a minimum:
#
# {
#   "api_key": "__your_api_key",
#   "form_name": "your form name",
# }
#################################################################################
@http_router.post('/upload_template/')
async def upload_template(file: UploadFile = File(...),
                          api_key: str = Form(...),
                          template_name: str = Form(...),
                          template_description: str = Form(...)
                          ):
    file_name = file.filename

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        while content := await file.read(1024):
            temp_file.write(content)
            temp_file_path = temp_file.name

    t = KineticPdf.upload_template(temp_file_path, file_name, api_key, template_name, template_description)

    return {"filename": file.filename, "id": template_name}

#
# Register by uploading a registration form.
#

@http_router.post("/register/")
async def register(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        while content := await file.read(1024):
            temp_file.write(content)
            temp_file_path = temp_file.name

    t = KineticPdf.registration_form(temp_file_path)

    return {"filename": file.filename, "id": t}


@http_router.post('/process/')
async def process_pdf_form(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        while content := await file.read(1024):
            temp_file.write(content)
            temp_file_path = temp_file.name

    t = KineticPdf.process_pdf_form(temp_file_path)

    return {"data": {"filename": file.filename, "id": t }, "error_code": "0", "error_msg": ""}


@http_router.post("/generate-pdf/")
async def generate_pdf(request: Request):

    json_data = await request.json()

    if "data" not in json_data:
        raise HTTPException(status_code=400, detail="JSON must contain 'data'.")

    if "id" not in json_data:
        raise HTTPException(status_code=400, detail="JSON['data'] must contain 'id'.")

    try:
        # file_name, pdf_file_path = KineticPdf.load_pdf_form(json_data)
        pdf_file_path, file_name = KineticPdf.load_pdf_form(json_data)
        return FileResponse(pdf_file_path, media_type='application/pdf', filename=f'{file_name}')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="PDF file not found.")

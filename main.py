###########################################################################################################
# KineticForms API Engine
#
# Copyright (c) 2023 - Kinetic Seas Inc.
#
# main.py - Main FastAPI Project File.
#
###########################################################################################################
from fastapi import FastAPI
from routers import pdf_router, auth_router, data_router, email_router, http_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Replace with necessary origins to avoid CORS errors.
origins = [
    "http://localhost:4200",
    "https://pdfforms.org",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers in the request
)

app.include_router(pdf_router)     # Include routes related to creating and loading PDFs.
app.include_router(auth_router)    # Include routes related to authorization and API management.
app.include_router(data_router)    # Include routes for database (CRUD) operations.
app.include_router(email_router)   # Include routes for email processing.
app.include_router(http_router)    # Include routes for API Upload/Download/File processing.

###########################################################################################################
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the
# following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial
# portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###########################################################################################################

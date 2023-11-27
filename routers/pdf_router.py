from fastapi import FastAPI, File, UploadFile, APIRouter
import tempfile
from processpdf import ProcessPdf

pdf_router = APIRouter()

#################################################################################
# Get a single pre-populated form by querying the pdf_form_data table for a
# specific app_id.
#
# The application requires a JSON string that provides the information required
# to get the template, query the database, and return a file.
#################################################################################



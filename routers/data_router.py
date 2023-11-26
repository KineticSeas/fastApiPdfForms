import json

from fastapi import FastAPI, File, UploadFile, APIRouter, Request
from processpdf import ProcessPdf
from queries import Queries

data_router = APIRouter()

DB_CONNECTION_VAULT = "/var/pwd.json"

#################################################################################
# Get data from uploaded forms for an organization.
# Since this application was developed with Angular in mind, there is a
# single parameter that is a JSON string.
#
# It requires a valid API key with 'full' or 'read' access to access the data.
# If no other parameters are passed, the endpoint will return all forms accessable
# by the API key provided.
#
# "form_id" returns all forms with the form_id provided.
# "app_id" returns all forms with the app_id provided.
#################################################################################
# /get_data/ :
# /list_forms/ :
# /

#@data_router.post('/list_templates/')
#async def template_list(request: Request):
#    json_data = await request.json()
#    d = KineticPdf.get_template_list(json_data)
#    return {"data": d, "error_code": "0", "error_msg": ""}


#################################################################################
# Delete a template from an organizations account.
#
# The parameter is a JSON string with the containing your API key and the
# form_id of the template you want to delete.
#
# {
#   "api_key": "__your_api_key",
#   "form_id": 999
# }
#################################################################################

#@data_router.post('/delete_template')
#async def list_forms(json: str):
#    return KineticPdf.delete_template(json)

#################################################################################
# Delete uploaded form data from the pdf_form_data table.
#
# The parameter is a JSON string with the containing your API key, "form_id"
# if you want all data for a specific form deleted, "app_id" to delete a
# specific uploaded form.
#
# {
#   "api_key": "__your_api_key",
#   "form_id": 999
# }
#################################################################################
#@data_router.post('/delete_form_data/')
#async def delete_form_data(json: str):
#    return KineticPdf.delete_form_data(json)


#@data_router.post('/create_form/')
#async def create_form(json: str):
#    return KineticPdf.get_form(json)

@data_router.post("/get_form_data")
async def get_form_data(private_key: str):
    q = Queries(DB_CONNECTION_VAULT)
    j = {"private_key": private_key }
    return {"error_code": "0", "error_msg": "", "data": q.get_data(json.dumps(j)) }

@data_router.post("/json_get_form_data/")
async def get_data(j: str):
    q = Queries(DB_CONNECTION_VAULT)
    return {"error_code": "0", "error_msg": "", "data": q.get_data(j) }


@data_router.post("/json_load_form/")
async def json_load_form(j: str):
    return {"error_code": "0", "error_msg": "", "data": ProcessPdf.json_load_form_sql(j) }

####@data_router.post('/guest-download/')
####async def create_user(request: Request):
####    json_data = await request.json()
####    d = KineticPdf.get_guest_xls(json_data['data'])
####    return d

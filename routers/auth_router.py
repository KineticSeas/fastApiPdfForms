from fastapi import FastAPI, File, UploadFile, APIRouter, Request
from kineticauth import KineticAuth
from processpdf import ProcessPdf
from kineticpdf import KineticPdf
auth_router = APIRouter()
import json


##################################################################################
# ORGANIZATION CRUD
##################################################################################

#@auth_router.post('/create_org/')
#async def create_org(request: Request):
#    j_data = await request.json()
#    return KineticAuth.create_org(j_data)


#@auth_router.post('/update_org/')
#async def update_org(request: Request):
#    j_data = await request.json()
#    return KineticAuth.update_org(j_data)


#@auth_router.post('/get_org/')
#async def get_org(request: Request):
#    j_data = await request.json()
#    return KineticAuth.get_org(j_data)


#@auth_router.post('/get_org_list/')
#async def get_org_list(request: Request):
#    j_data = await request.json()
#    return KineticAuth.get_org_list(j_data)


#@auth_router.post('/delete_org/')
#async def delete_org(request: Request):
#    j_data = await request.json()
#    return KineticAuth.delete_org(j_data)


#################################################################################
# USER CRUD
#################################################################################

#@auth_router.post('/create_user/')
#async def create_user(request: Request):
#    json_data = await request.json()
#    d = KineticAuth.create_user(json_data)
#    if d['error_code'] == '0':
#        return d
#    else:
#        return {"data": "", "error_code": d['error_code'], "error_msg": d['error_msg']}

#@auth_router.post('/get_user_list/')
#async def get_user_list(request: Request):
#    json_data = await request.json()
#    d = KineticAuth.get_user_list(json_data)
#    if d['error_code'] == '0':
#        return d
#    else:
#        return {"data": "", "error_code": d['error_code'], "error_msg": d['error_msg']}

#@auth_router.post('/update_user/')
#async def get_user_list(request: Request):
#    json_data = await request.json()
#    return KineticAuth.update_user(json_data)

#@auth_router.post('/get_user/')
#async def get_user(request: Request):
#    json_data = await request.json()
#    return KineticAuth.get_user(json_data)


#@auth_router.post('/delete_user/')
#async def delete_user(request: Request):
#    json_data = await request.json()
#    return KineticAuth.delete_user(json_data)


###############################################################
# USER PRIVILEGES
###############################################################

#@auth_router.post('/get_user_privs/')
#async def get_user_privs(request: Request):
#    json_data = await request.json()
#    return KineticAuth.get_user_privs(json_data)


#@auth_router.post('/add_user_priv/')
#async def get_user_priv(request: Request):
#    json_data = await request.json()
#    return KineticAuth.add_user_priv(json_data)


#@auth_router.post('/revoke_user_priv/')
#async def revoke_user_priv(request: Request):
#    json_data = await request.json()
#    return KineticAuth.revoke_user_priv(json_data)


###############################################################
# API KEYS
################################################################

#@auth_router.post('/create_api_key/')
#async def create_api_key(request: Request):
#    json_data = await request.json()
#    return KineticAuth.create_api_key(json_data)


#@auth_router.post('/revoke_api_key/')
#async def revoke_api_key(request: Request):
#    j_data = await request.json()
#    return KineticAuth.revoke_api_key(j_data)


@auth_router.post('/create_guest_key/')
async def create_guest_key(request: Request):
    j_data = await request.json()
    json_data = j_data['data']
    client_host = request.client.host
    user_agent = request.headers.get('user-agent')
    json_data['user_agent'] = user_agent
    json_data['client_host'] = client_host
    return KineticAuth.create_guest_key(json_data)


@auth_router.post('/guest-login/')
async def process_guest_login(request: Request):
    j_data = await request.json()
    json_data = j_data['data']
    client_host = request.client.host
    user_agent = request.headers.get('user-agent')
    json_data['user_agent'] = user_agent
    json_data['client_host'] = client_host
    return KineticAuth.process_guest_login(json_data)


@auth_router.post('/guest-forms/')
async def get_guest_login(request: Request):
    j_data = await request.json()
    json_data = j_data['data']
    client_host = request.client.host
    user_agent = request.headers.get('user-agent')
    json_data['user_agent'] = user_agent
    json_data['client_host'] = client_host
    return ProcessPdf.get_guest_forms(json_data)

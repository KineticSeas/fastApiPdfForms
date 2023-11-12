from fastapi import FastAPI, File, UploadFile, APIRouter, Request
from kineticauth import KineticAuth
from kineticpdf import KineticPdf
auth_router = APIRouter()
import json


#################################################################################
# USER CRUD
#################################################################################

@auth_router.post('/create_user/')
async def create_user(request: Request):
    json_data = await request.json()
    d = KineticAuth.create_user(json_data)
    if d['error_code'] == '0':
        return d
    else:
        return {"data": "", "error_code": d['error_code'], "error_msg": d['error_msg']}


@auth_router.post('/get_user_list/')
async def get_user_list(request: Request):
    json_data = await request.json()
    d = KineticAuth.get_user_list(json_data)
    if d['error_code'] == '0':
        return d
    else:
        return {"data": "", "error_code": d['error_code'], "error_msg": d['error_msg']}


@auth_router.post('/update_user/')
async def update_user(json: str):
    return KineticAuth.update_user(json)


@auth_router.post('/get_user/')
async def get_user(json: str):
    return KineticAuth.get_user(json)





@auth_router.post('/delete_user/')
async def delete_user(json: str):
    return KineticAuth.delete_user(json)


###############################################################
# USER PRIVILEGES
###############################################################

@auth_router.post('/get_user_privs/')
async def get_user_privs(json: str):
    return KineticAuth.get_user_privs(json)


@auth_router.post('/add_user_priv/')
async def get_user_priv(json: str):
    return KineticAuth.add_user_priv(json)


@auth_router.post('/revoke_user_priv/')
async def revoke_user_priv(json: str):
    return KineticAuth.revoke_user_priv(json)


###############################################################
# API KEYS
################################################################

@auth_router.post('/create_api_key/')
async def create_api_key(json: str):
    return KineticAuth.create_api_key(json)


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
    return KineticPdf.get_guest_forms(json_data)

@auth_router.post('/revoke_api_key/')
async def revoke_api_key(json: str):
    return KineticAuth.revoke_api_key(json)


##################################################################################
# ORGANIZATION CRUD
##################################################################################


@auth_router.post('/create_org/')
async def create_org(json: str):
    return KineticAuth.create_org(json)


@auth_router.post('/update_org/')
async def update_org(json: str):
    return KineticAuth.update_org(json)


@auth_router.post('/get_org/')
async def get_org(json: str):
    return KineticAuth.get_org(json)


@auth_router.post('/get_org_list/')
async def get_org_list(json: str):
    return KineticAuth.get_org_list(json)


@auth_router.post('/delete_org/')
async def delete_org(json: str):
    return KineticAuth.delete_org(json)


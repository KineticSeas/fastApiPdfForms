from kineticemail import KineticImapEmail
from fastapi import FastAPI, File, UploadFile, APIRouter, Form, HTTPException, Request

email_router = APIRouter()


@email_router.get('/process-cron/')
async def process_cron():
    json_data = {
        "connection_path": "/var/emailpwd.json",
        "output_path": "/var/html/docs"
    }
    d = KineticImapEmail.process_inbox_batch(json_data)
    return {"data": d, "error_code": "0", "error_msg": ""}

@email_router.post('/process-forms/')
async def process_forms(request: Request):
    json_data = await request.json()
    d = KineticImapEmail.process_inbox_batch(json_data)
    return {"data": d, "error_code": "0", "error_msg": ""}


@email_router.post('/create_email_account/')
async def process_email():
    return KineticImapEmail.process_inbox_batch('/var/emailpwd.json')


@email_router.post("/email-form/")
async def email_form():
    j = {}
    return KineticImapEmail.email_form(j)


@email_router.post('/get-mail/')
async def get_mail(request: Request):
    json_data = await request.json()
    d = KineticImapEmail.get_messages(json_data)
    return {"data": d, "error_code": "0", "error_msg": ""}


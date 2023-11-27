from processemail import ProcessEmail, ProcessExternalEmail
from kineticforms import KineticForms
from kineticemail import KineticEmail
from fastapi import FastAPI, File, UploadFile, APIRouter, Form, HTTPException, Request

email_router = APIRouter()

EMAIL_CONNECTION_VAULT = '/var/gptpwd.json'
DB_CONNECTION_VAULT = '/var/pwd.json'
ATTACHMENT_PATH = '/Users/user/Downloads'

#@email_router.get('/process-cron/')
#async def process_cron():
#    json_data = {
#        "connection_path": "/var/emailpwd.json",
#        "output_path": "/var/html/docs"
#    }
#    d = KineticImapEmail.process_inbox_batch(json_data)
#    return {"data": d, "error_code": "0", "error_msg": ""}


@email_router.post('/process-all-mailboxes/')
async def process_all_mailboxes():
    pe = ProcessExternalEmail()
    d = pe.get_mailbox_list()
    return {"data": d, "error_code": "0", "error_msg": ""}

@email_router.post('/process-forms/')
async def process_forms(request: Request):
    # json_data = await request.json()
    pe = ProcessEmail(EMAIL_CONNECTION_VAULT, EMAIL_CONNECTION_VAULT,ATTACHMENT_PATH)
    d = pe.process_inbox_batch()
    return {"data": d, "error_code": "0", "error_msg": ""}


@email_router.post('/process-chatgpt/')
async def process_chatgpt(request: Request):
    pe = ProcessEmail(DB_CONNECTION_VAULT, EMAIL_CONNECTION_VAULT, None)
    d = pe.process_inbox_chatgpt()
    return {"data": d, "error_code": "0", "error_msg": ""}


#@email_router.post('/reply-to-old/')
#async def process_forms(request: Request):
#    kf = KineticForms(DB_CONNECTION_VAULT)
#    sql = "select * from pdf_processed_email order by id"
#    rs = kf.sql(sql)
#    ke = KineticEmail(EMAIL_CONNECTION_VAULT)
#    for i in rs['data']:
#        message_id = i['message_id']
##        msg = ke.get_message_by_id(message_id,"Inbox")
#        ke.reply_to_email(msg, "This is reply from the nested functions", None)
#    return {"C":"C"}


#@email_router.post('/create_email_account/')
#async def process_email():
#    return ProcessEmail.process_inbox_batch(EMAIL_CONNECTION_VAULT)

@email_router.post('/clear_touch/')
async def clear_touch():
    kf = KineticForms('/var/pwd.json')
    return kf.clear_touch()


#@email_router.post("/email-form/")
#async def email_form():
#    j = {}
#    return ProcessEmail.email_form(j)


#@email_router.post('/get-mail/')
#async def get_mail(request: Request):
#    json_data = await request.json()
#    d = ProcessEmail.get_messages(json_data)
#    return {"data": d, "error_code": "0", "error_msg": ""}


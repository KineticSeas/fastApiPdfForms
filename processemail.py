###########################################################################################################
# KineticForms API Engine
#
# Copyright (c) 2023 - Kinetic Seas Inc.
# by Edward Honour and Joseph Lehman.
#
# email_router.py - Main FastAPI Project File.
#
# Optional Routes for Processing PDF Files using email.
###########################################################################################################
from pathlib import Path
from kineticglue import KineticGlue
from kineticforms import KineticForms
from kineticemail import KineticEmail
from chatgpt import MyOpenAI
import json

EMAIL_CONNECTION_VAULT = '/var/gptpwd.json'
DB_CONNECTION_VAULT = '/var/pwd.json'


class ProcessEmail:

    def __init__(self, db_connection_path, email_connection_path, attachment_path):
        # db_connection_path can be a str or dict.
        # email_connection_path can be a str or dict.
        self.kg = KineticGlue(db_connection_path, email_connection_path)
        self.kf = KineticForms(db_connection_path)
        self.ke = KineticEmail(email_connection_path)
        self.db_connection_path = db_connection_path
        self.email_connection_path = email_connection_path
        self.attachment_path = attachment_path
        pass


    def is_email_processed(self, message):
        sql = "select count(*) as c from pdf_processed_email where attachment_file_name = '"
        sql += "' and processed = 'Y'"
        count = self.kf.sql0(sql)
        if count['c'] > 0:
            return True
        else:
            return False

    def is_attachment_processed(self, attachment_file_name):
        sql = "select count(*) as c from pdf_processed_email where attachment_file_name = '" + str(f)
        sql += "' and processed = 'Y'"
        count = self.kf.sql0(sql)
        if count['c'] > 0:
            return True
        else:
            return False

    def get_user_from_pdf_key(self, msg):
        if "Author" in msg:
            sql = "select * from pdf_api_key"
            rs = self.kf.sql(sql)
            for i in rs['data']:
                public_key = i['public_key']
                if public_key in msg['Author']:
                    return {"public_key": i['public_key'], "private_key": i['private_key'], "user_id": i['user_id'],
                            "form_key": i['id'] }
            return {"public_key": "", "private_key": "", "user_id": 0, "form_key": 0}
        else:
            return {"public_key": "", "private_key": "", "user_id": 0, "form_key": 0}

    def save_pdf_form(self, msg):

        if "pdf_file_path" not in msg:
            return {"error_code": "9900", "error_msg": "No Form Processed", "data": {}}

        # Get User from recipient_email
        # Get User from original_recipient_email
        # Get User from Author Key

        if 'Author' not in msg:
            msg['Author'] = ''
        if 'Title' not in msg:
            msg['Title'] = ''


        y = self.get_user_from_pdf_key(msg)

        public_key = y['public_key']
        private_key = y['private_key']
        user_id = y['user_id']
        form_id = y['form_key']

        touch = { "pdf_file_path": msg['pdf_file_path'] }

        if msg['forwarded'] == 'N':
            msg['original_sender'] = msg['from_address']
            msg['original_recipient'] = msg['to_address']

        if not self.kf.touched(touch):
            post = {
                "table_name": "pdf_form_data",
                "action": "insert",
                "id": "",
                "user_id": user_id,
                "org_id": 0,
                "title": msg['Title'],
                "author": msg['Author'],
                "form_id": form_id,
                "private_key": private_key,
                "public_key": public_key,
                "metadata_json": "",
                "data_json": json.dumps(msg),
                "email_from": msg['from_address'],
                "email_to": msg['to_address'],
                "forwarded": msg['forwarded'],
                "original_email_from": msg['original_sender'],
                "original_email_to": msg['original_recipient'],
                "pdf_file_path": msg['pdf_file_path'],
                "email_subject": msg['subject'],
                "message_id": msg['message_id'],
                "email_body": msg['body']
            }
            y = self.kf.post(post)
            if y['error_code'] == "0":
                self.kf.touch(touch)
                return y
        else:
            return {"error_code": "0", "error_msg": "", "data": {}}


    def save_processed_email(self, msg):

        if "pdf_file_path" not in msg:
            msg['pdf_file_path'] = ""

        post = {
            "table_name": "pdf_processed_email",
            "action": "insert",
            "id": "",
            "message_id": msg['message_id'],
            "from_address": msg['from_address'],
            "to_address": msg['to_address'],
            "message_number": msg['message_number'],
            "forwarded": msg['forwarded'],
            "original_sender": msg['original_sender'],
            "original_recipient": msg['original_recipient'],
            "subject": msg['subject'],
            "body": msg['body'],
            "attachment_file_name": msg['pdf_file_path'],
            "processed": "Y",
            "form_data_id": "0"
        }
        self.kf.post(post)

    def message_function(self, message):
        print('Processing Message')
        if self.kf.touched(message):
            print('message was processed')
        else:
            if 'pdf_file_path' in message:
                self.ke.reply_to_email(message['message_id'], "Your form has been received.")
            self.save_processed_email(message)
            self.kf.touch(message)

    def blank_attachment(self, message):
        print('Processing Blank Attachment')
        message['blank_attachment'] = 'Yes'
        if self.kf.touched(message):
            pass
        else:
            print('This EMAIL HAS A BLANK ATTACHMENT')
            self.kf.touch(message)

    def no_attachment(self, message):
        print('Processing No Attachment')
        message['no_attachment'] = 'Yes'
        if self.kf.touched(message):
            pass
        else:
            print(message)
            self.ke.reply_to_email(message['message_id'], "The email you sent has no PDF attachment.")
            print('This EMAIL HAS NO ATTACHMENT')
            self.kf.touch(message)

    def attachment_function(self, message):
        print('Processing Attachment')
        self.save_pdf_form(message)

    def process_inbox_batch(self):
        ##
        ## Called by endpoint
        ##
        list = self.kg.post_pdf_email(self.attachment_path, "Inbox", self.message_function,
                                      self.attachment_function, noatttachment_function=self.no_attachment,
                                      blankattachment_function=self.blank_attachment)
        return list

    def process_inbox_chatgpt(self):
        ##
        ## Called by endpoint
        ##

        gpt = MyOpenAI(DB_CONNECTION_VAULT)

        list = self.ke.get_mailbox_messages('','Inbox',None, None)
        for i in list['data']:
            if not self.kf.touched(i):
                response = gpt.chat(i['from_address'], i['body'], i['message_id'])
                self.kf.touch(i)

class ProcessExternalEmail():

    def __init__(self):
        self.kf = KineticForms(DB_CONNECTION_VAULT)
        pass

    def get_mailbox_list(self):
        sql = "select * from pdf_mailbox where automatic = 'Y' order by id"
        rs = self.kf.sql(sql)
        data = rs['data']
        for i in data:
            pe = ProcessEmail(DB_CONNECTION_VAULT, i, i['attachment_path'])
            pe.process_inbox_batch()
        return data


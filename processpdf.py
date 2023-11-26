import pdfrw

import json
import shutil
import os
from pathlib import Path
import PyPDF2
from openpyxl import Workbook
import base64
import pikepdf
from kineticpdf import KineticPdf
from kineticauth import KineticAuth
from kineticforms import KineticForms
import copy

from openpyxl.utils import get_column_letter

DB_CONNECTION_VAULT = "/var/pwd.json"

class ProcessPdf:

    def __init__(self):
        pass

    @staticmethod
    def upload_template(temp_file_path, file_name, api_key, template_name, template_description):

        base_path = '/var/www/templates/'
        user = KineticAuth.get_user_from_api_key(api_key)
        user_id = user['id']

        dir_path = Path(base_path + str(user_id))
        dir_path.mkdir(parents=True, exist_ok=True)

        new_filename = base_path + str(user_id) + "/" + file_name

        with open(temp_file_path, 'rb') as temp_file:
            # Open the new file in 'write-binary' mode
            with open(new_filename, 'wb') as new_file:
                # Copy the temp file to the new file
                shutil.copyfileobj(temp_file, new_file)

        post = {
            "table_name": "pdf_template",
            "action": "insert",
            "id": "",
            "path": new_filename,
            "user_id": str(user_id),
            "template_name": template_name,
            "template_description": template_description
        }
        i = SqlData.post(post)

        return {"id": i}

    @staticmethod
    def json_load_form_sql(j):
        kf = KineticForms(DB_CONNECTION_VAULT)
        if not isinstance(j, dict):
            j = json.loads(j)

        form_key = j['form_key']
        template_path = j['template_path']

        sql = "select * from pdf_form_data where id = " + str(form_key)

        rs = kf.sql0(sql)
        values = rs['data']['data_json']
        values = json.loads(values)

        origin = copy.deepcopy(values)
        if "message_number" in values:
            del values['message_number']
        if "from_address" in values:
            del values['from_address']
        if "to_address" in values:
            del values['to_address']
        if "forwarded" in values:
            del values['forwarded']
        if "original_sender" in values:
            del values['original_sender']
        if "original_recipient" in values:
            del values['original_recipient']
        if "subject" in values:
            del values['subject']
        if "body" in values:
            del values['body']
        if "Author" in values:
            del values['Author']
        if "CreationDate" in values:
            del values['CreationDate']
        if "ModDate" in values:
            del values['ModDate']
        if "Keywords" in values:
            del values['Keywords']
        if "Producer" in values:
            del values['Producer']
        if "pdf_file_path" in values:
            del values['pdf_file_path']

        r = KineticPdf.fill_pdf_form('/Users/user/Downloads/Big Test PDF Form.pdf','/Users/user/Downloads/a.pdf', values, None)
        return { "k": r }

    #########################################################################
    # Get completed form data for entire API key, form_id, or app_id
    #
    # parameters = {
    #   api_key: "xxxxxxxxxxx",
    #   form_id: 999,
    #   app_id: 999
    # }
    #########################################################################
    @staticmethod
    def get_data(j: str):
        #
        # Convert JSON string parameter to dict.
        #
        parameters = json.loads(j)

        #
        #  Validate the API key.  If an error is return, return the error.
        #
        api = KineticAuth.check_api_key(parameters, 'read')
        if api['error'] != '':
            return {"error": api['error'], "data": []}


        user_id = api['user_id']
        org_id = api['org_id']

        #
        # Build the query string. If we don't have form_id, user_id,
        # app_id, or org_id in parameters, use the org_id from
        # the api_key and return everything.
        #
        flag = False
        sql = "select * from pdf_form_data where 1 = 1 "
        if "form_id" in parameters:
            sql+= "and form_id = " + str(parameters['form_id'])
            flag = True

        if "user_id" in parameters:
            sql+= "and user_id = " + str(parameters['user_id'])
            flag = True

        if "app_id" in parameters:
            sql+= "and app_id = " + str(parameters['app_id'])
            flag = True

        if "org_id" in parameters:
            sql+= "and org_id = " + str(parameters['org_id'])
            flag = True

        if not flag:
            sql+="and org_id = " + str(org_id)

        #
        # Execute the query.
        #
        recordset = SqlData.sql(sql)
        output = []
        for record in recordset:
            r={}
            r['create_timestamp'] = record['create_timestamp']
            r['form_id'] = record['form_id']
            r['app_id'] = record['app_id']
            r['title'] = record['title']
            r['author'] = record['author']
            r['metadata'] = json.loads(record['metadata_json'])
            r['formdata'] = json.loads(record['data_json'])
            output.append(r)

        return output


    ##############################################################################
    # Register a new organization and primary contact user by uploading a
    # registration form.
    ##############################################################################
    @staticmethod
    def registration_form(path):
        # Process the form like a standard form so we can debug issue later.
        KineticPdf.process_pdf_form(path)

        # Get the metadata
        metadata = KineticPdf.get_pdf_metadata(path)

        if metadata['Subject'] != "Registration Form":
            return {"error": "Invalid Form - Document Properties [Subject] Must be 'Registration Form'"}

        metadata_json = json.dumps(metadata)
        formdata = KineticPdf.get_form_fields(path)

        flag = False
        errors = []
        if formdata['first_name'] == '' or formdata['last_name'] == '':
            errors.append("Primary Contact First Name and Last Name must be entered")
            flag = True

        if formdata['email'] == '':
            errors.append("Primary Contact Email must be entered")
            flag = True

        if formdata['phone'] == '':
            errors.append("Primary Contact Phone must be entered")
            flag = True

        if flag:
            return {"errors": errors}

        # default fields from the KS Registration form
        primary_contact = {
            "salutation": formdata['salutation'],
            "first_name": formdata['first_name'],
            "last_name": formdata['last_name'],
            "company": formdata['company'],
            "email": formdata['email'],
            "phone": formdata['phone']
        }

        response = KineticAuth.create_organization(primary_contact)
        if response['org_id'] == 0:
            return {"errors": response['errors']}

        org_id = response['org_id']
        primary_contact['org_id'] = org_id

        response = KineticAuth.create_user(primary_contact)
        if response['user_id'] == 0:
            return {"errors": response['errors']}

        user_id = response['user_id']
        KineticAuth.create_api_key(org_id, user_id, ["full"])

        if formdata['first_name'] != '' and formdata['last_name'] != '' and formdata['email'] != '' and formdata['phone'] != '':
            technical_contact = {
                "salutation": formdata['salutation_tc'],
                "first_name": formdata['first_name_tc'],
                "last_name": formdata['last_name_tc'],
                "company": formdata['company'],
                "email": formdata['email_tc'],
                "phone": formdata['phone_tc'],
                "org_id": org_id
            }
            user_id = KineticAuth.create_user(technical_contact)
        else:
            technical_contact = {
                "salutation": "",
                "first_name": "",
                "last_name": "",
                "company": "",
                "email": "",
                "phone": "",
                "org_id": ""
            }

        KineticAuth.create_api_key(org_id, user_id, ["full"])
        return {"errors": [], "primary_contact": primary_contact, "technical_contact": technical_contact }

    @staticmethod
    def delete_template(j):
        pass


    @staticmethod
    def delete_form_data(j):
        pass

    @staticmethod
    def get_template_list(j: str):

        if 'api_key' not in j:
            return {"error": "Missing API Key"}

        if 'id' not in j:
            j['id'] = ""

        api = KineticAuth.check_api_key(j, 'read')
        if api['error'] != '':
            return {"error": api['error']}
        #
        # Convert input parameter from JSON to dict.
        #

        sql = "select * from pdf_template where 1 = 1 "
        if "user_id" in j:
            sql+= "and user_id = " + str(j['user_id'])


        recordset = SqlData.sql(sql)

        return recordset

    @staticmethod
    def get_guest_xls(j):

        results = {"error_code": 0, "error_msg": "", "data": j}

        if 'public_key' not in j:
            results = {"error_code": 101, "error_msg": "Missing Public Key", "data": {}}
            return results
        else:
            public_key = j['public_key']

        if 'private_key' not in j:
            results = {"error_code": 101, "error_msg": "Missing Private Key", "data": {}}
            return results
        else:
            private_key = j['private_key']

        if 'email' not in j:
            results = {"error_code": 101, "error_msg": "Missing Email", "data": {}}
            return results
        else:
            email = j['email']

        sql = "select * from pdf_form_data where form_id = '" + str(public_key) + "' order by id desc"
        print(sql)

        recordset = SqlData.sql(sql)
        output = []
        counter = 0
        for record in recordset:
            if counter == 0:
                r=[]
                for i in record:
                    if i == 'metadata_json' or i == 'data_json':
                        tmp = json.loads(record[i])
                        for j in tmp:
                            if j == 'Keywords':
                                for k in tmp['Keywords']:
                                    if '=' in k:
                                        key, value = k.split('=')
                                        r.append(key)
                                    else:
                                        r.append('Keyword')
                            else:
                                if isinstance(j, list):
                                    r.append(json.loads(j))
                                elif isinstance(j, dict):
                                    r.append(json.loads(j))
                                else:
                                    r.append(j)
                    else:
                        if isinstance(i, list):
                            r.append("")
                        elif isinstance(i, dict):
                            r.append("")
                        else:
                            r.append(i)

                output.append(r)
            counter += 1
            r = []
            for i in record:
                if i == 'metadata_json' or i == 'data_json':
                    tmp = json.loads(record[i])
                    for j in tmp:
                        if j == 'Keywords':
                            for k in tmp['Keywords']:
                                if '=' in k:
                                    key, value = k.split('=')
                                    r.append(value)
                                else:
                                    r.append(k)
                        else:
                            # r.append("DDD")
                            if type(tmp[j]) is not dict:
                                r.append(tmp[j])
                            else:
                                pass

                else:
                    if isinstance(i, list):
                        r.append(json.dumps(record[i]))
                    elif isinstance(record[i], dict):
                        r.append(json.dumps(record[i]))
                    else:
                        r.append(record[i])

            output.append(r)

        wb = Workbook()
        ws = wb.active
        results = []
        for row in output:
            j = []
            for o in range(0,len(row)):
                if isinstance(row[o], list):
                    k = json.dumps(row[o])
                elif isinstance(row[o], dict):
                    k = json.dumps(row[o])
                else:
                    k = row[o]
                j.append(k)

            results.append(j)
            ws.append(j)

        wb.save('/var/www/docs/' + public_key + '.xlsx')
        return results


    @staticmethod
    def get_guest_forms(j):

        results = {"error_code": 0, "error_msg": "", "data": j}

        if 'public_key' not in j:
            results = {"error_code": 101, "error_msg": "Missing Public Key", "data": {}}
            return results
        else:
            public_key = j['public_key']

        if 'private_key' not in j:
            results = {"error_code": 101, "error_msg": "Missing Private Key", "data": {}}
            return results
        else:
            private_key = j['private_key']

        if 'email' not in j:
            results = {"error_code": 101, "error_msg": "Missing Email", "data": {}}
            return results
        else:
            email = j['email']

        sql = "select * from pdf_form_data where form_id = '" + str(public_key) + "' order by id desc"
        print(sql)
        recordset = SqlData.sql(sql)
        output = []
        for record in recordset:
            r={}
            r['id'] = record['id']
            r['create_timestamp'] = record['create_timestamp']
            r['form_id'] = record['form_id']
            r['email_from'] = record['email_from']
            r['email_to'] = record['email_to']
            r['email_subject'] = record['email_subject']
            r['email_body'] = record['email_body']
            r['data_json'] = record['data_json']
            output.append(r)

        results['data'] = output
        return results

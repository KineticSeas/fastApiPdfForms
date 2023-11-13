import pdfrw
from kineticauth import KineticAuth
from sqldata import SqlData
import json
import shutil
import os
from pathlib import Path
import PyPDF2
from openpyxl import Workbook
import base64
import pikepdf

from openpyxl.utils import get_column_letter

class KineticPdf:

    def __init__(self):
        pass

    @staticmethod
    def is_pdf_encrypted(pdf_path):
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            return pdf_reader.is_encrypted

    @staticmethod
    def decrypt_pdf(input_path, output_path, pwd):
        with pikepdf.Pdf.open(input_path, password=pwd) as pdf:
            pdf.save('output.pdf')

    @staticmethod
    def convert_to_base64(binary_data):
        if isinstance(binary_data, bytes) or isinstance(binary_data, bytearray):
            return base64.b64encode(binary_data).decode('utf-8')
        return binary_data

    @staticmethod
    def read_pdf_signature(pdf_path):
        # Open the PDF
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            signatures = []

            for i in range(0, len(pdf_reader.pages)):
                page = pdf_reader._get_page(i)
                try:
                    annotations = page['/Annots']
                    for annotation in annotations:
                        obj = annotation.get_object()
                        if '/Subtype' in obj and obj['/Subtype'] == '/Widget' and '/AP' in obj and '/V' in obj:
                            ap = obj['/V']
                            r = ap.get_object()
                            if isinstance(r, PyPDF2.generic.DictionaryObject):
                                keys = list(r.keys())
                                if '/Type' in r:
                                    print(r)
                                    if r['/Type'] in ['/Signature', '/Signature2', '/Sig']:
                                        processed_annotation = {k: KineticPdf.convert_to_base64(v) for k, v in r.items()}
                                        signatures.append(processed_annotation)
                except KeyError:
                    pass  # No annotations on this page
        return signatures

    @staticmethod
    def set_radio_button_value(annotation, parent, desired_value):
        if annotation.get('/Parent') == parent:
            if '/' in desired_value:
                d = desired_value[1:]
            else:
                d = desired_value

            parent.update(pdfrw.PdfDict(V=pdfrw.PdfName(d)))
            parent.update(pdfrw.PdfDict(AS=pdfrw.PdfName(d)))
            if annotation['/AP']['/D']:
                if desired_value in annotation['/AP']['/D']:
                    annotation.update(pdfrw.PdfDict(V=pdfrw.PdfName('On')))
                    annotation.update(pdfrw.PdfDict(AS=pdfrw.PdfName(d)))
                else:
                    pass
                # annotation.update(pdfrw.PdfDict(AS=pdfrw.PdfName('/Off')))

    #
    # Extract text from a pdf
    #
    @staticmethod
    def extract_pdf_text(path):
        # Extract text from a PDF and return in a list of pages.

        # with open(path, 'rb') as file:
        results = []
        #    r = PyPDF2.PdfReader(file)
        #    for i in range(0, len(r.pages)):
        #        text = r.pages[i].extract_text()
        #        results.append(text)
        return results

    #
    # Extract images from a pdf
    #
    @staticmethod
    def extract_pdf_images(path):
        # with open(path, 'rb') as file:
            field_values = {}
        #    r = PyPDF2.PdfReader(file)
        #    if not r.get_fields():
            return field_values

    #
    # Extract table from a pdf
    #
    @staticmethod
    def extract_pdf_table(path):
        # with open(path, 'rb') as file:
        field_values = {}
        #     r = PyPDF2.PdfReader(file)
        #     if not r.get_fields():
        return field_values


    @staticmethod
    def load_pdf_form(j):

        if 'api_key' not in j:
            return "error", "Missing API Key"

        api = KineticAuth.check_api_key(j, 'read')
        if api['error'] != '':
            return "error", api['error']

        data = j['data']

        new_values = data
        template_id = j['id']

        sql="select * from pdf_template where id = " + str(template_id)
        rs=SqlData.sql0(sql)

        file_path = rs['path']

        output_file_name= j['file_name']
        new_values = j['data']
        output_pdf_path = "/var/www/tmp" + output_file_name
        output_file_name = KineticPdf.update_pdf_form(file_path, output_pdf_path, new_values)
        return output_file_name, output_pdf_path

    @staticmethod
    def update_pdf_form(input_pdf_path, output_pdf_path, new_values):

        print(new_values)

        reader = pdfrw.PdfReader(input_pdf_path)

        if '/AcroForm' in reader.Root:
            reader.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))

        # Iterate through each page and update form fields
        for page in reader.pages:
            annotations = page['/Annots']
            if annotations:
                for annotation in annotations:

                    if annotation['/Subtype'] == '/Widget':
                        print(annotation)
                        for key in new_values:

                            if annotation['/T']:

                                field_name = annotation['/T'][1:-1]  # Remove parentheses around field name
                                if field_name == key:
                                    print('T:' + new_values[key])
                                    annotation.update(pdfrw.PdfDict(V=new_values[key]))  # Set new value
                                    annotation.update(pdfrw.PdfDict(AP=''))
                                    new_value = new_values[key]
                                    annotation.update(pdfrw.PdfDict(AS=pdfrw.PdfName(new_value)))

                                    annotation.update(pdfrw.PdfDict(V='Dr'))

                                    if annotation['/FT'] == '/Btn' and '/AS' in annotation:
                                        new_value = new_values[key]
                                        print("X" + new_values[key])
                                        annotation.update(pdfrw.PdfDict(V=pdfrw.PdfName(new_value)))
                                        annotation.update(pdfrw.PdfDict(AS=pdfrw.PdfName(new_value)))
                                        annotation.update(pdfrw.PdfDict(AP=''))
                            else:
                                if annotation['/Parent']:
                                    parent = annotation['/Parent']
                                    if isinstance(parent, pdfrw.PdfDict) and '/T' in parent:
                                        my_name = parent['/T'][1:-1]
                                        if my_name == key:
                                            print('Not Update:' + new_values[key])
                                            new_value = new_values[key]
                                            annotation.update(
                                                pdfrw.PdfDict(V='{}'.format(new_value))
                                            )
                                            KineticPdf.set_radio_button_value(annotation, annotation['/Parent'], new_value)
                                            parent.update(pdfrw.PdfDict(V=new_values[key]))  # Set new value
                                            parent.update(pdfrw.PdfDict(AP=''))
                                            parent.update(pdfrw.PdfDict(AS=pdfrw.PdfName(new_value)))
                                            annotation.update(pdfrw.PdfDict(V=new_values[key]))  # Set new value
                                            annotation.update(pdfrw.PdfDict(AP=''))
                                            annotation.update(pdfrw.PdfDict(AS=pdfrw.PdfName(new_value)))

        pdfrw.PdfWriter().write(output_pdf_path, reader)

        return output_pdf_path

    @staticmethod
    def get_form_fields(infile):
        """
        Extract form fields and their values from a PDF.
        """
        form_fields = {}
        annotations = pdfrw.PdfReader(infile).Root.AcroForm.Fields
        for annotation in annotations:
            if annotation.FT == '/Tx':  # Field Type is Text
                key = annotation.T[1:-1]  # Remove parentheses around the key
                value = annotation.V[1:-1] if annotation.V else None  # Remove parentheses around the value
                form_fields[key] = value
            elif annotation.FT == '/Btn':  # Field Type is Button (Checkboxes and Radio buttons)
                key = annotation.T[1:-1]
                value = annotation.V
                form_fields[key] = value
            # Add more field types (like /Ch for choice fields) as needed
        return form_fields

    @staticmethod
    def get_pdf_metadata(infile):
        metadata = {}
        pdf = pdfrw.PdfReader(infile)
        info = pdf.Info
        if info:
            for key in info.keys():
                cleaned_key = key[1:]  # Remove '/' from the key
                value = info[key]
                if value:
                    # Remove starting and ending parentheses if present
                    if value.startswith('(') and value.endswith(')'):
                        value = value[1:-1]
                    # Process keywords
                    if cleaned_key == "Keywords":
                        metadata[cleaned_key] = [keyword.strip() for keyword in value.split(",")]
                    else:
                        metadata[cleaned_key] = value
                else:
                    metadata[cleaned_key] = None

            if 'Keywords' in metadata:
                keywords_list = metadata['Keywords']

                keywords_dict = {}
                for keyword in keywords_list:
                    key, value = keyword.split('=')
                    keywords_dict[key] = value

                metadata['keys'] = keywords_dict

        return metadata



    ########################################################################
    # Generic Upload and Process Form.  Metadata and Form Data are extracted
    # using pdfrw library and stored in the pdf_form_data table. All
    # metadata from the document is stored in metadata_json as a JSON
    # string and form data is stored in data_json as a JSON string.
    # Author and Title are added as separate columns.
    #
    # Metadata keywords should contain the form_id or the form and a
    # primary key in the app_id keyword. For example "form_id=1" tells
    # the function what template it is, and "app_id=1" tells us we are
    # updating an existing record "1" if it exists.  If it doesn't exist
    # record "1" will be created.
    ########################################################################
    @staticmethod
    def process_pdf_form(path, email):

        # Extract Metadata into a dict variable.

        metadata = KineticPdf.get_pdf_metadata(path)

        # Convert dict variable to a JSON string.
        metadata_json = json.dumps(metadata)

        # Extract Form Fields into a dict variable.
        formdata = KineticPdf.get_form_fields(path)

        # Convert dict variable to a JSON string.
        formdata_json = json.dumps(formdata)

        if metadata['keys']:
            if metadata['keys']['app_id']:
                app_id = metadata['keys']['app_id']
            else:
                app_id = 0

            if metadata['keys']['user_id']:
                user_id = metadata['keys']['user_id']
            else:
                user_id = 0

            if metadata['keys']['form_id']:
                form_id = metadata['keys']['form_id']
            else:
                form_id = 0
        else:
            app_id = 0
            user_id = 0
            form_id = 0

        if metadata['Title']:
            title = metadata['Title']
        else:
            title = ""

        public_key = ""
        private_key = ""

        if metadata['Author']:
            author = metadata['Author']
        else:
            author = ""

        print('author')
        print(author)

        if author != '':
            sql = "select id, public_key, private_key from pdf_api_key where status = 'active'"
            rs = SqlData.sql(sql)
            print(rs)
            for i in rs:
                print(i['public_key'])
                print(author)
                if i['public_key'] in author:
                    public_key = i['public_key']
                    private_key = i['private_key']

        # Create SQLData dict object to insert record into database.
        print(email)
        post_form = { "id": "",
                      "table_name": "pdf_form_data",
                      "action": "insert",
                      "user_id": user_id,
                      "form_id": public_key,
                      "title": title,
                      "author": author,
                      "private_key": private_key,
                      "email_from": email['from_address'],
                      "email_to": email['to_address'],
                      "email_subject": email['subject'],
                      "email_body": email['body'],
                      "metadata_json": metadata_json,
                      "data_json": formdata_json}

        # Insert record and return primary key.
        i = SqlData.post(post_form)

        return {"id": i}

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
    def load_form(template_path, output_path, sql):
        template_path = 'euc-hockey-form-blank.pdf'
        sql = "select data_json from kseas_form_data where id = 15"
        rs = SqlData.sql0(sql)
        values = rs
        return KineticPdf.update_pdf_form(template_path,'new2.pdf', json.loads(values['data_json']))

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

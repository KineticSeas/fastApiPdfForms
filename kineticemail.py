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
import json
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import socket
from email.header import decode_header
from pathlib import Path
from sqldata import SqlData
from kineticpdf import KineticPdf
import tempfile
import smtplib
from email.message import EmailMessage
import os
from bs4 import BeautifulSoup

#
# Kinetic Email Class contains basic email processing functions not specific to this
# project.
#
class KineticEmail:

    def __init__(self, connection_path):
        pass

    #
    # Generic function to connect to imap Email
    #
    @staticmethod
    def connect_imap(server, email_address, email_password):
        try:
            imap = imaplib.IMAP4_SSL(server)
            imap.login(email_address, email_password)
            return imap
        except imaplib.IMAP4.abort as e:
            return {"error": f"IMAP4 connection aborted: {e}"}
        except imaplib.IMAP4.error as e:
            return {"error": f"IMAP4 error occurred: {e}"}
        except socket.gaierror as e:
            return {"error": f"Address-related socket error occurred: {e}"}
        except socket.timeout as e:
            return {"error": f"Socket timeout occurred: {e}"}
        except socket.error as e:
            return {"error": f"Socket error occurred: {e}"}
        except Exception as e:  # A generic catch-all for any other exceptions
            return {"error": f"An unexpected error occurred: {e}"}

    @staticmethod
    def connect_smtp(server, email_address, email_password, port):
        server = smtplib.SMTP(server, port)
        server.starttls()
        server.login(email_address, email_password)
        return server

    #
    # Connect to imap email server using credentials from a JSON file located
    # on your local filesystem.  Make sure the file is not in http accessable
    # directory.
    #
    @staticmethod
    def auto_connect_imap(connection_vault_path):
        try:
            with open(connection_vault_path, 'r') as connection_file:
                connection_dict = json.load(connection_file)
                return KineticEmail.connect_imap(
                    connection_dict['imap_server'],
                    connection_dict['email_address'],
                    connection_dict['email_password']
                )
        except FileNotFoundError:
            return {"error": f"File '{connection_vault_path}' not found."}
        except json.JSONDecodeError as e:
            return {"error": f"Error decoding JSON: {e}"}

    @staticmethod
    def auto_connect_smtp(connection_vault_path):
        try:
            with open(connection_vault_path, 'r') as connection_file:
                connection_dict = json.load(connection_file)
                return KineticEmail.connect_smtp(
                    connection_dict['smtp_server'],
                    connection_dict['email_address'],
                    connection_dict['email_password'],
                    connection_dict['smtp_port']
                )
        except FileNotFoundError:
            return {"error": f"File '{connection_vault_path}' not found."}
        except json.JSONDecodeError as e:
            return {"error": f"Error decoding JSON: {e}"}


    #
    # Connect to imap email server using credentials provided by the
    # user at runtime.
    #
    @staticmethod
    def password_connect_imap(imap_server, email_address, email_password):
        return KineticEmail.connect_imap(
                imap_server,
                email_address,
                email_password
        )

    @staticmethod
    def password_connect_smtp(smtp_server, email_address, email_password, port):
        return KineticEmail.connect_smtp(
                smtp_server,
                email_address,
                email_password,
                port
        )

    #
    # Function to download an attachment from an email and save to
    # the filesystem.
    #
    @staticmethod
    def download_attachment(cls, emailPart, file_path):
        output_file_name = file_path + '/' + emailPart.get_filename()
        open(output_file_name, 'wb').write(emailPart.get_payload(decode=True))
        return output_file_name

    #
    # Function to move a file from one folder (mailbox) to another.
    #
    @staticmethod
    def move_file(self, imap, messageNum, targetMailbox):
        status, email_data = imap.fetch(messageNum, '(UID)')
        uid = email_data[0].split()[-1].decode("utf-8")  # Get the UID
        uid = uid[:-1]
        a, b = imap.uid('COPY', uid, targetMailbox)
        self.imap.uid('STORE', uid, '+FLAGS', '(\Deleted)')

    #
    # Get all messages from an imap mailbox and return the
    # status of the mailbox request and messages.
    #
    @staticmethod
    def get_imap_messages(imap, mailbox):
        imap.select(mailbox)    # Inbox
        status, messages = imap.search(None, "ALL")
        # status, messages = imap.search(None, 'SUBJECT "Email"')
        return status, messages

    #
    # Process all message dfrom an imap server.
    # Legacy POC code.
    #
    @staticmethod
    def download_email_attachments(imap, msgnums):
        for msgnum in msgnums[0].split():
            _, data = imap.fetch(msgnum, '(BODY.PEEK[])')
            message = email.message_from_bytes(data[0][1])
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    pass
                if part.get_content_maintype() != "multipart" and part.get('Content-Disposition') is not None:
                    KineticEmail.download_attachment(part, "/tmp")

            # target_mailbox = "NewFolder"
            # move_file(imap, msgnum, target_mailbox)

    #
    # Close the imap mailbox connection.
    #
    @staticmethod
    def close_imap_mail(imap):
        imap.expunge()
        imap.close()
        imap.logout()

#########################################################################################################
# The KineticImapEmail class contains functions to process emails from an imap email server.
#########################################################################################################
class KineticImapEmail():
    def __init__(self):
        pass

    #
    # Get all messages from the inbox and return a list of messages to potentially process.
    # This function returns of list of dict objects.
    #
    # Parameter 1:  Path to the connection vault file.
    # Parameter 2: (optional) Path where attachments are extracted to.
    #
    # THIS IS NOT CALLED DIRECTLY FROM AN ENDPOINT.
    #
    @staticmethod
    def get_messages(data):
        j = data['data']

        connection_vault_path = '/Users/user/emailpwd.json'

        if 'imap_server' in j:
            imap_server = j['imap_server']
            email_address = j['email_address']
            email_password = j['email_password']
            mailbox = j['mailbox']
        else:
            try:
                with open(connection_vault_path, 'r') as connection_file:
                    connection_dict = json.load(connection_file)
                    imap_server = connection_dict['imap_server']
                    email_address = connection_dict['email_address']
                    email_password = connection_dict['email_password']
                    mailbox = connection_dict['mailbox']
            except FileNotFoundError:
                return {"error": f"File '{connection_vault_path}' not found."}
            except json.JSONDecodeError as e:
                return {"error": f"Error decoding JSON: {e}"}

        if 'mailbox' not in j:
            return {"error": "must specify inbox"}

        imap = KineticEmail.password_connect_imap(imap_server, email_address, email_password)
        status, messages = KineticEmail.get_imap_messages(imap, mailbox)
        email_data = []

        if status == 'OK':
            message_numbers = messages[0].split()
            for num in message_numbers:
                body = ""
                status, data = imap.fetch(num, '(BODY.PEEK[])')
                if status == 'OK':
                    msg = email.message_from_bytes(data[0][1])
                    message_id = msg.get('Message-ID')
                    message_id = message_id.strip('<>') if message_id else "unknown"
                    to_address = msg.get('To')
                    from_address = msg.get('From')
                    subject = decode_header(msg["subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()

                    sender = decode_header(msg.get("From"))[0][0]
                    if isinstance(sender, bytes):
                        sender = sender.decode()
                    attachment_count = 0
                    attachment_filenames = []

                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                body = part.get_payload(decode=True).decode()
                            elif content_type == "text/html":
                                # Get the HTML body
                                body = part.get_payload(decode=True).decode()

                            if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                                continue
                            disposition = part.get('Content-Disposition')
                            if 'attachment' in disposition or 'filename' in disposition:
                                filename = part.get_filename()
                                if filename:
                                    filename = decode_header(filename)[0][0]
                                    if isinstance(filename, bytes):
                                        filename = filename.decode()
                                        output_file_name = filename
                                        attachment_filenames.append(output_file_name)
                            attachment_count += 1
                    else:

                        payload = msg.get_payload(decode=True).decode()
                        if msg.get_content_type() == "text/plain":
                            body = payload
                        else:
                            body = payload

                        if msg.get_content_maintype() != 'text' and msg.get('Content-Disposition') is not None:
                            filename = msg.get_filename()
                            if filename:
                                filename = decode_header(filename)[0][0]
                                if isinstance(filename, bytes):
                                    filename = filename.decode()
                                    attachment_filenames.append(filename)
                                attachment_count += 1

                    email_data.append({'message_number': num.decode(),
                                       'message_id': message_id,
                                       'subject': subject,
                                       'sender': sender,
                                       'from_address': from_address,
                                       'to_address': to_address,
                                       'msg': body,
                                       'attachment_count': attachment_count,
                                       "attachments": attachment_filenames})

        return email_data

    @staticmethod
    def get_inbox_messages(connection_vault_path, attachment_path='', mailbox="Inbox"):

        # To use username/password authentication change here.
        imap = KineticEmail.auto_connect_imap(connection_vault_path)
        print(imap)
        #
        # Get the mailbox status and all directories from the inbox.
        #
        status, messages = KineticEmail.get_imap_messages(imap, mailbox)

        # list to return data.
        email_data = []

        #
        # only process if retrieval is OK.
        #
        if status == 'OK':
            #
            # Convert the result list to individual message numbers
            #
            message_numbers = messages[0].split()

            #
            # Process each email.
            for num in message_numbers:
                # Fetch the email by its number (RFC822 protocol for full email)
                # status, data = imap.fetch(num, '(RFC822)')
                status, data = imap.fetch(num, '(BODY.PEEK[])')
                if status == 'OK':
                    # Parse the email content
                    msg = email.message_from_bytes(data[0][1])

                    #
                    # Get message id, recipient email, subject, and sender
                    #
                    message_id = msg.get('Message-ID')
                    message_id = message_id.strip('<>') if message_id else "unknown"
                    to_address = msg.get('To')

                    subject = decode_header(msg["subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()

                    sender = decode_header(msg.get("From"))[0][0]
                    if isinstance(sender, bytes):
                        sender = sender.decode()

                    # Count and download attachments.
                    #
                    # Only download attachments if a path was specified.
                    #
                    # Initialize attachment count
                    body = ""
                    attachment_count = 0
                    attachment_filenames = []
                    #
                    # Both single part and multipart emails may have attachments.
                    #      We only download multipart.
                    #
                    if msg.is_multipart():
                        for part in msg.walk():
                            #
                            # Check if part is an attachment
                            #
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                body = part.get_payload(decode=True).decode()

                                # Extracting HTML content and converting it to text
                            elif content_type == "text/html":
                                html_content = part.get_payload(decode=True).decode()
                                soup = BeautifulSoup(html_content, "html.parser")
                                body = soup.get_text()

                            if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                                continue
                            disposition = part.get('Content-Disposition')
                            if 'attachment' in disposition or 'filename' in disposition:
                                filename = part.get_filename()
                                print('filename')
                                if filename:
                                    print(filename)
                                    filename = decode_header(filename)[0][0]
                                    if isinstance(filename, bytes):
                                        filename = filename.decode()
                                    if '/' in filename:
                                        f = filename.split('/')
                                        filename = f[-1]
                                    print(filename)
                                    if attachment_path != '':
                                        output_file_name = attachment_path + '/' + message_id + '-' + filename
                                        file_path = Path(output_file_name)
                                        if not file_path.exists():
                                            open(output_file_name, 'wb').write(part.get_payload(decode=True))
                                    else:
                                        output_file_name = filename

                                    attachment_filenames.append(output_file_name)
                            attachment_count += 1
                    else:
                        #
                        # Email does not have multiple parts, so we can identify attachments but
                        # not download them.
                        #
                        payload = msg.get_payload(decode=True).decode()
                        if msg.get_content_type() == "text/plain":
                            body = payload
                            print("Plain text body:", body)
                        elif msg.get_content_type() == "text/html":
                            soup = BeautifulSoup(payload, "html.parser")
                            body = soup.get_text()
                            print("Text extracted from HTML body:", body)

                        if msg.get_content_maintype() != 'text' and msg.get('Content-Disposition') is not None:
                            filename = msg.get_filename()
                            if filename:
                                filename = decode_header(filename)[0][0]
                                if isinstance(filename, bytes):
                                    filename = filename.decode()

                                attachment_filenames.append("single-part:" + filename)
                            attachment_count += 1

                    # Append email to the list.
                    email_data.append({'message_number': num.decode(), 'subject': subject, 'sender': sender,
                                       'to_address': to_address,
                                       'body': body,
                                       'attachment_count': attachment_count,
                                       "attachments": attachment_filenames})

        return email_data

    @staticmethod
    def process_inbox_batch(json_data):
        connection_vault_path = json_data['connection_path']
        output_path = json_data['output_path']

        #
        # Get a batch of emails from the inbox.  This can be modified to pull from any
        # email folder,
        #
        batch = KineticImapEmail.get_inbox_messages(connection_vault_path, output_path)
        counter = 0
        for msg in batch:
            print(msg)
            for f in msg['attachments']:
                path = Path(f)
                if path.suffix.lower() == '.pdf':
                    #
                    # Check if already processed.
                    #
                    sql = "select count(*) as c from pdf_processed_email where attachment_file_name = '" + str(f)
                    sql += "' and processed = 'Y'"
                    count = SqlData.sql0(sql)
                    if count['c'] == 0:
                        #
                        # Not processed then use AppData.process_pdf_form to process the
                        # form data from the PDF.
                        #
                        e = {
                            'from_address': msg['sender'],
                            'to_address': msg['to_address'],
                            'subject': msg['subject'],
                            'body': msg['body']
                        }
                        i = KineticPdf.process_pdf_form(f, e)
                        if 'id' in i:
                            counter = counter + 1
                            #
                            # Create record to insert into database.
                            #
                            post = {
                                "table_name": "pdf_processed_email",
                                "action": "insert",
                                "id": "",
                                "from_address": msg['sender'],
                                "to_address": msg['to_address'],
                                "message_number": i['id'],
                                "body": msg['body'],
                                "subject": msg['subject'],
                                "attachment_file_name": "",
                                "processed": "Y",
                                "form_data_id": i['id']
                            }

                            post['message_number'] = i['id']
                            post['attachment_file_name'] = f
                            print(post)
                            #
                            # Insert into database.
                            #
                            SqlData.post(post)

        return {"forms": counter}

    @staticmethod
    def email_form(j):
        connection_vault_path = '/Users/user/emailpwd.json'
        with open(connection_vault_path, 'r') as connection_file:
            connection_dict = json.load(connection_file)


        # mail_from = j['from']
        # mail_to = j['to']
        # body = j['message']
        # subject = j['subject']
        # body = j['body']
        # path = j['path']
        #server = KineticEmail.auto_connect_smtp('/Users/user/emailpwd.json')
        # Create email message

        message = MIMEMultipart()
        # message['From'] = mail_from
        message['To'] = "testform@smtp.kineticforms.org"
        # message['To'] = mail_to
        message['From'] = "forms@smtp.kineticforms.org"
        # message['Subject'] = subject
        message['Subject'] = "This is a test"
        body = ""
        message.attach(MIMEText(body,'plain'))

        path="/Users/user/tmp/output.pdf"
        fn = path.split("/")[-1]

        with open(path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename= {fn}')
        message.attach(part)

        with smtplib.SMTP('kineticforms.org', 587) as server:
            server.starttls()
            server.login('forms@smtp.kineticforms.org', 'Loipol229!')
            server.send_message(message)

        # server.send_message(message)
        # server.quit()


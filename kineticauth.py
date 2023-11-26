###########################################################################################################
# KineticForms API Engine
#
# Copyright (c) 2023 - Kinetic Seas Inc.
#
# email_router.py - Main FastAPI Project File.
#
# Optional Routes for Processing PDF Files using email.
###########################################################################################################

from kineticforms import KineticForms
import json
import random
import hashlib
import tempfile

class KineticAuth:

    def __init__(self):
        self.kf = KineticForms('/var/pwd.json')

    def process_guest_login(self, j):
        results = {"error_code": 0, "error_msg": "", "data": {}}
        # Check that api_key is in dictionary passed in as j

        if 'public_key' not in j:
            results = {"error_code": 100, "error_msg": "Missing Public Key", "data": j}
            return results
        else:
            public_key = j['public_key']

        if 'private_key' not in j:
            results = {"error_code": 101, "error_msg": "Missing Private Key", "data": j}
            return results
        else:
            private_key = j['private_key']

        if 'email' not in j:
            results = {"error_code": 102, "error_msg": "Missing Email", "data": j}
            return results
        else:
            email = j['email'].lower()

        # Query the API key provided to make sure it is valid.
        sql = "select * from pdf_api_key where public_key = '" + str(public_key) + "' and "
        sql += " private_key = '" + str(private_key) + "' and email = '" + str(email) + "'"
        rs = self.kf.sql0(sql)

        if rs is not None:
            results = {"error_code": 0, "error_msg": "", "data": rs}
            return results
        else:
            results = {"error_code": 105, "error_msg": "Invalid, email, public_key, private_key combination.", "data": {}}
            return results


    def check_api_key(self, j, priv):
        results = {"user_id": 0, "org_id": 0, "privs": [], "error": ""}

        if 'api_key' not in j:
            results['error'] = "Missing API Key"
            return results
        else:
            key = j['api_key']

        sql = "select * from pdf_api_key where api_key = '" + key + "'"
        rs = self.kf.sql0(sql)

        if rs is not None:
            if rs['status'] != 'active':
                results['error'] = "API Key is not active."
                return results
        else:
            results['error'] = "Invalid API Key"
            return results

        user_id = rs['user_id']
        sql = "select * from pdf_user where id = " + str(rs['user_id'])
        user = self.kf.sql0(sql)

        user_id = 0
        if user:

            if user['status'] != 'active':
                results['error'] = "User Account is not Active"
                return results
            else:
                user_id = user['id']
                results['org_id'] = user['org_id']
        else:
            results['error'] = "User Account is not Active"
            return results

        results['user_id'] = rs['user_id']
        results['org_id'] = user['org_id']

        privs = []
        sql = "select priv_id from pdf_api_priv where key_id = " + str(rs['id'])
        rs2 = self.kf.sql(sql)
        if rs2:
            for i in rs2:
                privs.append(i['priv_id'])

        results['privs'] = privs

        if priv == 'self':
            if user_id != j['id']:
                results['error'] = "Key does not have necessary privileges for this action."
                return results
        else:
            if priv not in privs and 'full' not in privs:
                results['error'] = "Key does not have necessary privileges for this action."
                return results
            else:
                return results

    def get_user_sql(self, user_id):
        sql = "select * from pdf_user where id = " + str(user_id)
        record = self.kf.sql0(sql)
        return record

    def get_user_from_api_key(api_key):
        j = {"api_key": api_key}
        u = KineticAuth.check_api_key(j, "read")
        return KineticAuth.get_user_sql(u['user_id'])


    ###################################################################
    # Create user with API (not form upload)
    ###################################################################
    @staticmethod
    def create_user_api(j):
        #
        # Validate the API Key to have full or admin privs
        #
        if 'api_key' not in j:
            return {"error": "Missing API Key"}

        if 'id' not in j:
            j['id'] = ""

        api = KineticAuth.check_api_key(j, 'admin')
        if api['error'] != '':
            return {"error": api['error']}

        return KineticAuth.create_user(j)

    @staticmethod
    def get_user_list(j):
        api = KineticAuth.check_api_key(j, 'admin')
        if api['error'] != '':
            return {"data": api['error'], "error_code": "404", "error_msg": api['error']}

        sql = "select * from pdf_user order by last_name"
        rs = SqlData.sql(sql)
        return {"data": rs, "error_code": "0", "error_msg": ""}

    @staticmethod
    def create_user(j):

        api = KineticAuth.check_api_key(j, 'admin')
        if api != '':
            return {"data": {}, "error_code": "404", "error_msg": api}
        contact = j['data']
        return KineticAuth.process_create_user(contact)

    @staticmethod
    def process_create_user(contact):

        if 'id' in contact:
            id = contact['id']
        else:
            id = ""

        if 'company_name' not in contact:
            contact['company_name'] = ''
        if 'first_name' not in contact:
            contact['first_name'] = ''
        if 'org_id' not in contact:
            contact['org_id'] = 0

        post_form = {"id": id,
                     "table_name": "pdf_user",
                     "action": "insert",
                     "company_name": contact['company_name'],
                     "org_id": contact['org_id'],
                     "first_name": contact['first_name'],
                     "last_name": contact['last_name'],
                     "salutation": contact['salutation'],
                     "email": contact['email'].lower(),
                     "phone": contact['phone']
                     }

        #
        # Make sure no user exists with the email and phone provided.
        #
        flag = False
        err = ""
        sql = "select count(*) as c from pdf_user where email = '" + contact['email'].lower() + "'"
        rs = SqlData.sql0(sql)
        if rs['c'] > 0:
            err += "User Exists with this Email Address "
            flag = True

        #
        # If no errors create the user.
        #
        user_id = 0
        if not flag:
            user_id = SqlData.post(post_form)
        else:
            return {"data": {}, "error_code": "400", "error_msg": err}

        return {"data": {"user_id": user_id}, "error_code": "0", "error_msg": err}


    @staticmethod
    def delete_user(j):

        user = j['user']

        api = KineticAuth.check_api_key(user, 'admin')
        if api['error'] != '':
            return {"error": api['error']}

        sql = "update pdf_user set status = 'deleted' where id = " + str(user['id'])
        if 'final' in user:
            if user['final'] == 'Y':
                sql = "delete from pdf_user where id = " + str(user['id'])

        SqlData.execute(sql)

        return {"org_id": user['id'], "error": ""}

    @staticmethod
    def update_user(j):
        #
        # Validate the API Key to have full or admin privs, or self.
        #
        if 'api_key' not in j:
            return {"error": "Missing API Key"}

        if 'id' not in j:
            return {"error": "ID must be provided to edit user."}

        api = KineticAuth.check_api_key(j, 'self')
        if api['error'] != '' and api['user_id'] != j['id']:
            return {"error": api['error']}

        return KineticAuth.create_user(j)

    @staticmethod
    def add_user_priv(j):
        pass

    @staticmethod
    def revoke_user_priv(j):
        pass

    @staticmethod
    def get_user(j):
        pass

    ###################################################################
    # Edit user with API (not form upload)
    ###################################################################
    @staticmethod
    def edit_user(j):
        #
        # Validate the API Key to have full or admin privs, or self.
        #
        if 'api_key' not in j:
            return {"error": "Missing API Key"}

        if 'id' not in j:
            return {"error": "ID must be provided to edit user."}

        api = KineticAuth.check_api_key(j, 'self')
        if api['error'] != '' and api['user_id'] != j['id']:
            return {"error": api['error']}

        return KineticAuth.create_user(j)




    @staticmethod
    def get_user_privs(j):
        pass

    @staticmethod
    def revoke_api_key(j):
        pass

    @staticmethod
    def get_api_key(j):
        pass

    @staticmethod
    def create_org(j):
        org = j['organization']
        return KineticAuth.create_organization(org)

    @staticmethod
    def update_org(j):
        org_id = j['org_id']
        return KineticAuth.edit_organization(org_id)

    @staticmethod
    def delete_org(j):
        org_id = j['org_id']
        return KineticAuth.delete_organization(org_id)

    @staticmethod
    def get_org(j):
        pass

    @staticmethod
    def get_org_list(j):
        pass


    ###############################################################################
    # Generate an API Key for a user.
    ###############################################################################
    @staticmethod
    def create_api_key(j):
        org_id = j['org_id']
        user_id = j['user_id']
        privs = j['privs']

        #
        # Generate an API key by concat 2 long random hex strings
        # and then extracting 32 chars out of a random position.
        # Randon number from 1 to ten million.
        #
        random_number = random.randint(1, 10000000)
        # SHA256 the number.
        string_to_hash = str(random_number)
        hash_object = hashlib.sha256()
        hash_object.update(string_to_hash.encode())
        hex_dig = hash_object.hexdigest()
        api_base = hex_dig

        # Generate another random number between 1 and ten million
        random_number = random.randint(1, 10000000)
        # SHA256 the second number.
        string_to_hash = str(random_number)
        hash_object = hashlib.sha256()
        hash_object.update(string_to_hash.encode())
        hex_dig = hash_object.hexdigest()

        # Concat the strings to create a 128 char string.
        api_base = api_base + hex_dig

        # Pick a random value in the first 64 chars.
        startpos = random.randint(1, 64)
        api_key = api_base[startpos:startpos + 32]

        # Post the API to the database.
        post_form = {"id": "",
                     "table_name": "pdf_api_key",
                     "action": "insert",
                     "user_id": user_id,
                     "org_id": org_id,
                     "api_key": api_key,
                     "status": 'active'
                     }

        key_id = SqlData.post(post_form)

        # Add records for each privilege.
        for priv in privs:
            post_form = {"id": "",
                         "table_name": "pdf_api_priv",
                         "action": "insert",
                         "key_id": key_id,
                         "priv_id": priv
                         }
            SqlData.post(post_form)

        return {"error": "0"}

    @staticmethod
    def create_guest_key(j):

        # return {"data": j, "error_code": "100", "error_msg": "Error: Email Address is required."}

        kf = KineticForms('/var/pwd.json')

        email = j['email']
        first_name = j['first_name']
        org_name = j['org_name']
        last_name = j['last_name']
        user_agent = j['user_agent']
        privs = ["full", "admin"]

        client_host = j['client_host']

        if email == '':
            return {"data": {}, "error_code": "100", "error_msg": "Error: Email Address is required."}

        if first_name == '' or last_name =='':
            return {"data": {}, "error_code": "101", "error_msg": "Error: First Name and Last Name are Required."}
        sql = "select count(*) as c from pdf_blocked_email_address where email = '" + email.lower() + "'"
        rs = kf.sql0(sql)
        if str(rs['data']['c']) != "0":
            sql = "select count(*) as c from pdf_blocked_ip_address where ip = '" + client_host + "'"
            rs2 = kf.sql0(sql)
            if str(rs2['data']['c']) == "0":
                post_data = {
                    "table_name": "pdf_blocked_ip_address",
                    "action": "insert",
                    "id": "",
                    "email": email.lower(),
                    "ip": client_host
                }
                kf.post(post_data)
            return {"data": {}, "error_code": "901", "error_msg": "Email address blocked."}

        sql = "select count(*) as c from pdf_blocked_ip_address where ip = '" + client_host + "'"
        rs2 = kf.sql0(sql)
        if rs2['data']['c'] > 0:
            return {"data": {}, "error_code": "902", "error_msg": "IP address blocked."}

        #
        # Generate an API key by concat 2 long random hex strings
        # and then extracting 32 chars out of a random position.
        # Randon number from 1 to ten million.
        #
        random_number = random.randint(1, 10000000)
        # SHA256 the number.
        string_to_hash = str(random_number)
        hash_object = hashlib.sha256()
        hash_object.update(string_to_hash.encode())
        hex_dig = hash_object.hexdigest()
        api_base = hex_dig

        # Generate another random number between 1 and ten million
        random_number = random.randint(1, 10000000)
        # SHA256 the second number.
        string_to_hash = str(random_number)
        hash_object = hashlib.sha256()
        hash_object.update(string_to_hash.encode())
        hex_dig = hash_object.hexdigest()

        # Concat the strings to create a 128 char string.
        api_base = api_base + hex_dig

        # Pick a random value in the first 64 chars.
        startpos = random.randint(1, 64)
        private_key = api_base[startpos:startpos + 32]

        startpos = random.randint(65, 100)
        public_key = api_base[startpos:startpos + 6]

        # Post the API to the database.
        post_form = {"id": "",
                     "table_name": "pdf_api_key",
                     "action": "insert",
                     "user_id": "0",
                     "org_name": org_name,
                     "first_name": first_name,
                     "last_name": last_name,
                     "email": email,
                     "public_key": public_key,
                     "private_key": private_key,
                     "user_agent": user_agent,
                     "ip_address": client_host,
                     "status": 'active'
                     }
        print(post_form)
        kid = kf.post(post_form)
        key_id = kid['data']['id']

        # Add records for each privilege.
        for priv in privs:
            post_form = {"id": "",
                         "table_name": "pdf_api_priv",
                         "action": "insert",
                         "key_id": key_id,
                         "priv_id": priv
                         }
            print(post_form)
            kf.post(post_form)

        rs = {"private_key": private_key, "public_key": public_key }
        return {"data": rs, "error_code": "0", "error_msg": ""}

    ###############################################################################
    # Delete/Revoke all Keys for a User.
    ###############################################################################
    @staticmethod
    def delete_user_keys(key):

        api = KineticAuth.check_api_key(key, 'admin')
        if api['error'] != '':
            return {"error": api['error']}

        sql = "update pdf_api_key set status = 'deleted' where user_id = " + str(key['user_id'])
        if 'final' in key:
            if key['final'] == 'Y':
                sql = "delete from pdf_api_key where user_id = " + str(key['user_id'])

        SqlData.execute(sql)

        return {"user_id": key['user_id'], "error": ""}

    ###############################################################################
    # Delete/Revoke all Keys for a User.
    ###############################################################################
    @staticmethod
    def delete_key(key):

        api = KineticAuth.check_api_key(key, 'self')
        if api['error'] != '':
            return {"error": api['error']}

        sql = "update pdf_api_key set status = 'deleted' where api_key = '" + str(key['api_key']) + "'"
        if 'final' in key:
            if key['final'] == 'Y':
                sql = "delete from pdf_api_key  where api_key = '" + str(key['api_key']) + "'"

        SqlData.execute(sql)

        return {"api_key": key['api_key'], "error": ""}

    ###############################################################################
    # Delete an Organization
    ###############################################################################
    @staticmethod
    def delete_organization(org):

        api = KineticAuth.check_api_key(org, 'write')
        if api['error'] != '':
            return {"error": api['error']}

        sql = "update pdf_org set status = 'deleted' where id = " + str(org['id'])
        if 'final' in org:
            if org['final']=='Y':
                sql = "delete from pdf_org where id = " + str(org['id'])

        SqlData.execute(sql)

        return {"org_id": org['id'], "error": ""}

 ###############################################################################
    # Create an Organization
    ###############################################################################
    @staticmethod
    def create_organization(contact):
        #
        # Create the Post Data for SQL.
        #
        post_form = {"id": "",
                     "table_name": "pdf_org",
                     "action": "insert",
                     "organization_name": contact['company_name'],
                     "contact_first_name": contact['first_name'],
                     "contact_last_name": contact['last_name'],
                     "contact_salutation": contact['salutation'],
                     "contact_email": contact['email'].lower(),
                     "contact_phone": contact['phone'],
                     "status": "active"
                     }

        #
        # Check the Email and Phone for the Primary Contact do not already exist
        # on an existing organization.
        #
        flag = False
        err = []
        sql = "select count(*) as c from pdf_org where contact_email = '" + contact['email'].lower() + "'"
        rs = SqlData.sql0(sql)
        if rs['c'] > 0:
            err.append("Organization Exists with this Contact Email Address")
            flag = True

        sql = "select count(*) as c from pdf_org where contact_phone = '" + contact['phone'] + "'"
        rs = SqlData.sql0(sql)
        if rs['c'] > 0:
            err.append("Organization Exists with this Contact Phone Number")
            flag = True

        #
        # Post the Organization to the database.
        #
        org_id = 0
        if not flag:
            org_id = SqlData.post(post_form)

        return {"org_id": org_id, "errors": err}

    ###############################################################################
    # Edit an Organization
    # A valid API key with 'full' or 'write' privileges must be provided.
    ###############################################################################
    @staticmethod
    def edit_organization(org):

        api = KineticAuth.check_api_key(org, 'write')
        if api['error'] != '':
            return {"error": api['error']}
        #
        # Create the Post Data for SQL.
        #
        post_form = {"id": org['id'],
                     "table_name": "pdf_org",
                     "action": "insert",
                     "organization_name": org['company_name'],
                     "contact_first_name": org['first_name'],
                     "contact_last_name": org['last_name'],
                     "contact_salutation": org['salutation'],
                     "contact_email": org['email'].lower(),
                     "contact_phone": org['phone'],
                     "status": "active"
                     }

        org_id = SqlData.post(post_form)

        return {"org_id": org_id, "error": ""}

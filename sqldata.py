###########################################################################################################
# KineticForms API Engine
#
# Copyright (c) 2023 - Kinetic Seas Inc.
# by Edward Honour and Joseph Lehman.
#
# sqldata.py - Main FastAPI Project File.
#
# Optional Routes for Processing PDF Files using email.
#
#
###########################################################################################################
import json
import mysql.connector
import pymysql
import pymysql.cursors
from fastapi import FastAPI, Request, Response, HTTPException


class Db:
    # This is the connection class for MySQL.  If you are using a different database
    # change this function to connect properly.

    def __init__(self):
        pass

    @classmethod
    def connect(cls):
        connection_vault_path = '/var/pwd.json'

        try:
            with open(connection_vault_path, 'r') as connection_file:
                connection_dict = json.load(connection_file)
                print(connection_dict)

            return pymysql.connect(
                host=connection_dict['host'],
                user=connection_dict['user'],
                password=connection_dict['password'],
                database=connection_dict['database'],
                cursorclass=pymysql.cursors.DictCursor
            )
        except FileNotFoundError:
            print(f"File '{connection_vault_path}' not found.")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")


class SqlData(Db):
    # This is the a basic CRUD class for MySQL.  If you are using a different database
    # change this function to perform these operations.

    def __init__(self):
        super().__init__()

    # execute any query and return the results.

    @staticmethod
    def sql(s):
        try:
            conn = Db.connect()
        except mysql.connector.Error as err:
            error_info = {
                "error_number": err.errno,
                "sql_state": err.sqlstate,
                "message": err.msg
            }
            raise HTTPException(status_code=400, detail=error_info)
        try:
            cursor = conn.cursor()
        except mysql.connector.Error as err:
            # Returning an HTTPException with a JSON response
            error_info = {
                "error_number": err.errno,
                "sql_state": err.sqlstate,
                "message": err.msg
            }
            raise HTTPException(status_code=400, detail=error_info)
        try:
            cursor.execute(s)
        except mysql.connector.Error as err:
            # Returning an HTTPException with a JSON response
            error_info = {
                "error_number": err.errno,
                "sql_state": err.sqlstate,
                "message": err.msg
            }
            raise HTTPException(status_code=400, detail=error_info)
        try:
             records = cursor.fetchall()
        except mysql.connector.Error as err:
            # Returning an HTTPException with a JSON response
            error_info = {
                "error_number": err.errno,
                "sql_state": err.sqlstate,
                "message": err.msg
            }
            raise HTTPException(status_code=400, detail=error_info)
        return records


    @staticmethod
    def sql0(s):
        conn = Db.connect()
        cursor = conn.cursor()
        cursor.execute(s)
        records = cursor.fetchone()
        return records

    @staticmethod
    def sqlC(s):
        conn = Db.connect()
        cursor = conn.cursor()
        cursor.execute(s)
        records = cursor.fetchone()[0]
        return records

    @staticmethod
    def execute(s):
        conn = Db.connect()
        cursor = conn.cursor()
        cursor.execute(s)
        try:
            conn.commit()
        except:
            pass
        return

    @staticmethod
    def post(my_dict):

        try:
            if 'id' not in my_dict:
                my_id = 0
            else:
                my_id = my_dict['id']
        except:
            return {"s": "1"}

        try:
            if 'action' not in my_dict:
                my_action = "insert"
            else:
                my_action = my_dict['action']
        except:
            return {"s": "2"}

        try:
            if 'table_name' not in my_dict:
                return 900
            else:
                table_name = my_dict['table_name']
        except:
            return {"s": "3"}

        conn = Db.connect()
        cursor = conn.cursor()
        if my_action == 'insert' or my_action == 'update':
            if my_id == 0 or my_id == '':
                sql = "insert into " + table_name + "(create_timestamp) values (now())"
                cursor.execute(sql)
                conn.commit()
                cursor.execute("SELECT LAST_INSERT_ID()")
                m = cursor.fetchone()
                my_id = m['LAST_INSERT_ID()']
            for key in my_dict:
                if key != 'table_name' and key != 'id' and key != 'action':
                    cursor = conn.cursor()
                    sql = "update " + table_name + " set " + key + " = %s where id = %s"
                    print(sql)
                    v = (my_dict[key], my_id)
                    print(v)
                    cursor.execute(sql, v)
            conn.commit()
        if my_action == 'delete':
            sql = "delete from " + table_name + " where id = " + my_id
            cursor.execute(sql)

        return my_id

    @staticmethod
    def insert(table_name, json_data):
        my_dict = json.loads(json_data)
        conn = Db.connect()
        cursor = conn.cursor()

        sql = "insert into " + table_name
        cols = " (create_timestamp"
        vals = " values (now()"
        values = []
        for key, value in my_dict.items():
            if cols == " (":
                cols += key
            else:
                cols += " ," + key

            if vals == " (":
                vals += "%s"
            else:
                vals += ", %s"

            values.append(value)

        cols += ")"
        vals += ")"
        sql += cols + vals
        cursor.execute(sql, values)
        cursor.execute("SELECT LAST_INSERT_ID()")
        my_id = cursor.fetchone()[0]

        return my_id

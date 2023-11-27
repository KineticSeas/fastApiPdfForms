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
from kineticforms import KineticForms

from openpyxl.utils import get_column_letter

class Queries:

    def __init__(self, db_connection_path):
        self.kf = KineticForms(db_connection_path)
        self.db_connection_path = db_connection_path
        pass

    def get_data(self, j):
        jj = json.loads(j)
        private_key = jj['private_key']
        sql = "select * from pdf_form_data where private_key = '" + str(private_key) + "' order by id"
        rs = self.kf.sql(sql)
        output = []
        for i in rs['data']:
            print(i)
            jd = i['data_json']
            if jd != '':
                js_dict = json.loads(jd)
                d = {}
                for j in js_dict:
                    d[j] = js_dict[j]
                if "pdf_file_path" in d:
                    del d['pdf_file_path']
                output.append(d)
        return output

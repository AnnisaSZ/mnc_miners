from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,timedelta
from odoo.http import request
import requests
import logging


class BcrDateLock(Exception):

    def cek_date_lock_act(self,tipe, myid, date_act):
        if tipe:
            if tipe == "input":
                code = "DL01"
            elif tipe == "review":
                code = "DL02"
            elif tipe == "approve":
                code = "DL03"
            else:
                return True
            date_lock_par = request.env['bcr.parameter.setting'].sudo().search(
                [("code", "=", code), ("status", "=", True)])
            if not date_lock_par:
                return False
            cek_not_allow_user_ids = date_lock_par[0].not_allow_user_ids
            if myid in cek_not_allow_user_ids.ids:
                return False
            else:
                if tipe == "input":
                    h_par = date_lock_par[0].value
                    date_act = datetime.strptime(str(date_act), '%Y-%m-%d')
                    date_today = datetime.strptime(str(fields.Date.today()), '%Y-%m-%d')
                    dt = date_act - date_today
                    dt = int(dt.days)
                    if dt <= 0:
                        if dt < int(h_par):
                            return True
                        else:
                            return False
                    elif dt > 0:
                        if dt > int(h_par):
                            return True
                        else:
                            return False
                    else:
                        return True
                else:
                    h_par = date_lock_par[0].value
                    date_act = datetime.strptime(str(date_act), '%Y-%m-%d')
                    date_today = datetime.strptime(str(fields.Date.today()), '%Y-%m-%d')
                    end_date = date_act + timedelta(days=int(h_par))
                    # print(timedelta(days=int(h_par)))
                    dt = end_date - date_today
                    # print(int(dt.days))
                    if int(dt.days) >= 0:
                        return False
                    else:
                        return True
        else:
            return True

    def cek_date_lock_act_message(self,tipe):
        if tipe == "input":
            date_lock_par = request.env['bcr.parameter.setting'].sudo().search(
                [("code", "=", "DL01M")])
            if not date_lock_par:
                return "Not Found Message"
            return str(date_lock_par[0].value)
        elif tipe == "review":
            date_lock_par = request.env['bcr.parameter.setting'].sudo().search(
                [("code", "=", "DL02M")])
            if not date_lock_par:
                return "Not Found Message"
            return str(date_lock_par[0].value)
        elif tipe == "approve":
            date_lock_par = request.env['bcr.parameter.setting'].sudo().search(
                [("code", "=", "DL03M")])
            if not date_lock_par:
                return "Not Found Message"
            return str(date_lock_par[0].value)
        else:
            return "Not Found Message"
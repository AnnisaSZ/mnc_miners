from odoo import api, fields, models, _, tools
import datetime
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
import requests
import json
import numpy
import calendar
from dateutil import relativedelta

# URL Get DATA
_base_url_bspc = "http://bspc.mnc-coal.com/"
_base_url_pmc = "http://pmc.mnc-coal.com/"

_service = "a01/f0060310"

_security = "waoBvjiEIWKCE7ZDrX7Z86Hyf4SPcg71CYtpb4g0x1eD0g2ZoEJ1kwPQlv8sHAeGmHMpgSEzLAUhTTTwHa6WhHnQ1mTbtJF0SMhe"
_year = ["2021", "2022", "2023"]

_month = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
    "November", "December"]


class TimbanganDataWiz(models.TransientModel):
    _name = 'timbangan.vdata.wiz'

    name = fields.Char(string="Name", default="Get Data")

    def _get_test(self):
        print("TEST Scheduler")

    def get_month_number(self, month):
        return {
            'January': "01",
            'February': "02",
            'March': "03",
            'April': "04",
            'May': "05",
            'June': "06",
            'July': "07",
            'August': "08",
            'September': "09",
            'October': "10",
            'November': "11",
            'December': "12"
        }[month]

    def get_data_scheduler(self):
        curent_year = datetime.datetime.now().strftime("%Y")
        curent_month = datetime.datetime.now().strftime("%m")
        last_date_data = self.env['timbangan.vdata'].search([], order="tanggal desc",limit=1).tanggal
        last_date2_data = datetime.datetime.strptime(str(last_date_data), "%Y-%m-%d")

        # print(last_date2_data.year)
        # print(calendar.month_name[int(last_date2_data.month)])
        deldata = self.env['timbangan.vdata'].search([('tahun', '=', last_date2_data.year), ('bulan', '=', calendar.month_name[int(last_date2_data.month)]), ('bisnis_unit', 'in', ['BSPC', 'PMC'])]).unlink()
        if deldata:
            for y in _year:
                if int(y) < int(curent_year) or int(y) > int(curent_year):
                    continue
            for m in _month:
                if int(self.get_month_number(m)) < int(last_date2_data.month) or int(self.get_month_number(m)) > int(curent_month):
                    continue
               # print(m, "m")
               # self.get_action_data_api_bspc(y, m)
                self.get_action_data_api_pmc(y, m)

        return {
            'name': 'View Timbangan',
            'view_mode': 'tree,kanban',
            'res_model': 'timbangan.vdata',
            'type': 'ir.actions.act_window',
            'context': "{'search_default_group_by_bisnis_unit': True, 'search_default_group_by_tanggal':True}",
        }

    def get_data_scheduler_days(self):
        curent_year = datetime.datetime.now().strftime("%Y")
        curent_month = datetime.datetime.now().strftime("%B")
        curent_date = datetime.datetime.now().strftime('%Y-%m-%d')

        # curent_date = '2023-06-13'

        deldata = self.env['timbangan.vdata'].search([('tanggal', '=', curent_date), ('bisnis_unit', 'in', ['BSPC','PMC'])]).unlink()

        self.get_action_data_api_bspc_days_v2(curent_year, curent_month,curent_date)
        self.get_action_data_api_pmc_days(curent_year, curent_month, curent_date)

        return {
            'name': 'View Timbangan',
            'view_mode': 'tree,kanban',
            'res_model': 'timbangan.vdata',
            'type': 'ir.actions.act_window',
            'context': "{'search_default_group_by_bisnis_unit': True, 'search_default_group_by_tanggal':True}",
        }

    # ============= Get Data Daily ===================
    def get_data_bspc_scheduler_days(self):
        curent_year = datetime.datetime.now().strftime("%Y")
        curent_month = datetime.datetime.now().strftime("%B")
        curent_date = datetime.datetime.now().strftime('%Y-%m-%d')

        # curent_date = '2023-06-13'

        deldata = self.env['timbangan.vdata'].search([('tanggal', '=', curent_date), ('bisnis_unit', 'in', ['BSPC'])]).unlink()

        # self.get_action_data_api_bspc_days(curent_year,curent_month,curent_date)
        self.get_action_data_api_bspc_days_v2(curent_year, curent_month, curent_date)

        return {
            'name': 'View Timbangan',
            'view_mode': 'tree,kanban',
            'res_model': 'timbangan.vdata',
            'type': 'ir.actions.act_window',
            'context': "{'search_default_group_by_bisnis_unit': True, 'search_default_group_by_tanggal':True}",
        }

    def get_data_pmc_scheduler_days(self):
        curent_year = datetime.datetime.now().strftime("%Y")
        curent_month = datetime.datetime.now().strftime("%B")
        curent_date = datetime.datetime.now().strftime('%Y-%m-%d')
        print("====Next Date===")
        next_date = (datetime.datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        print(next_date)

        deldata = self.env['timbangan.vdata'].search([('tanggal', '=', curent_date), ('bisnis_unit', 'in', ['PMC'])]).unlink()

        # self.get_action_data_api_pmc_days(curent_year, curent_month, curent_date)
        self.get_action_data_api_pmc_days_v2(curent_year, curent_month, curent_date)

        return {
            'name': 'View Timbangan',
            'view_mode': 'tree,kanban',
            'res_model': 'timbangan.vdata',
            'type': 'ir.actions.act_window',
            'context': "{'search_default_group_by_bisnis_unit': True, 'search_default_group_by_tanggal':True}",
        }

    def get_data_ibpe_scheduler_days(self):
        curent_year = datetime.datetime.now().strftime("%Y")
        curent_month = datetime.datetime.now().strftime("%B")
        curent_date = datetime.datetime.now().strftime('%Y-%m-%d')
        next_date = (datetime.datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        deldata = self.env['timbangan.vdata'].search([('tanggal', '=', curent_date), ('bisnis_unit', 'in', ['IBPE'])]).unlink()

        # self.get_action_data_api_pmc_days(curent_year, curent_month, curent_date)
        self.get_action_data_api_ibpe_days_v2(curent_year, curent_month, curent_date)

        return {
            'name': 'View Timbangan',
            'view_mode': 'tree,kanban',
            'res_model': 'timbangan.vdata',
            'type': 'ir.actions.act_window',
            'context': "{'search_default_group_by_bisnis_unit': True, 'search_default_group_by_tanggal':True}",
        }
    # ============================================

    def get_action_data_api_bspc_days(self, year, month,date):
        headers = {'Security': _security}
        par_p001 = "refresh"
        par_f001 = "DAYS"
        par_f002 = year
        par_f003 = month
        params = {'p001': par_p001, 'f001': par_f001, 'f002': par_f002, 'f003': par_f003}
        url = _base_url_bspc + _service
        response = requests.post(url, params=params, headers=headers)
        data = json.loads(response.text)
        if (data["status"] == 1):
            if (data["data"]["x"]):
                dt = numpy.stack((numpy.array(data["data"]["x"]), numpy.array(data["data"]["val"])), axis=1)
                for list in dt:
                    split_date = list[0].split("-")
                    frm_data = split_date[2] + "-" + self.get_month_number(split_date[1]) + "-" + split_date[0]
                    if frm_data != date:
                        continue
                self.env['timbangan.vdata'].create({
                    'bisnis_unit': "BSPC",
                    'tanggal': frm_data,
                    'bulan': split_date[1],
                    'tahun': split_date[2],
                    'val_timbangan': list[1]
                })
            else:
                print(data, "Response Oke (Empty)")
        else:
            print(data, "Response Error")

    def get_action_data_api_pmc_days(self, year, month, date):
        headers = {'Security': _security}
        par_p001 = "refresh"
        par_f001 = "DAYS"
        par_f002 = year
        par_f003 = month
        params = {'p001': par_p001, 'f001': par_f001, 'f002': par_f002, 'f003': par_f003}
        url = _base_url_pmc + _service
        response = requests.post(url, params=params, headers=headers)
        data = json.loads(response.text)
        data = json.loads(response.text)
        if (data["status"] == 1):
            if (data["data"]["x"]):
                dt = numpy.stack((numpy.array(data["data"]["x"]), numpy.array(data["data"]["val"])), axis=1)
                for list in dt:
                    split_date = list[0].split("-")
                    frm_data = split_date[2] + "-" + self.get_month_number(split_date[1]) + "-" + split_date[0]
                    if frm_data != date:
                        continue
                    self.env['timbangan.vdata'].create({
                        'bisnis_unit': "PMC",
                        'tanggal': frm_data,
                        'bulan': split_date[1],
                        'tahun': split_date[2],
                        'val_timbangan': list[1]
                    })
            else:
               print(data, "Response Oke (Empty)")
        else:
            print(data, "Response Error")

    # ========== API Get New Version ==============
    # BSPC New Version
    def get_action_data_api_bspc_days_v2(self, year, month, date):
        headers = {'Security': _security}
        par_f001 = date
        par_f002 = date
        par_f003 = 'SEMUA'
        par_f004 = 'SEMUA'
        par_f005 = 'SEMUA'
        par_f006 = 'SEMUA'
        par_f007 = 'SEMUA'
        par_f008 = 'SEMUA'
        params = {'f001': par_f001, 'f002': par_f002, 'f003': par_f003, 'f004': par_f004, 'f005': par_f005, 'f006': par_f006, 'f007': par_f007, 'f008': par_f008}
        url = _base_url_bspc + _service
        response = requests.post(url, params=params, headers=headers)
        data = json.loads(response.text)
        if (data["status"] == 1):
            if (data["data"]["graph"]):
                data_val = 0
            for data_graph in data["data"]["graph"]:
                if data_graph['f001'] == 'BONGKAR':
                    data_val = data_val + data_graph['f003']
            print("XXXXXXXXXXXXXXXXXXXXX")
            print(data_val)
            self.env['timbangan.vdata'].create({
               'bisnis_unit': "BSPC",
               'tanggal': date,
               'bulan': month,
               'tahun': year,
               'val_timbangan': data_val
            })
    # PMC
    def get_action_data_api_pmc_days_v2(self, year, month, date):
        headers = {'Security': _security}
        print("Date:", date)
        print(type(date))
        par_f001 = date
        par_f002 = date
        par_f003 = 'PMC'
        par_f004 = 'SEMUA'
        par_f005 = 'SEMUA'
        par_f006 = 'SEMUA'
        par_f007 = 'SEMUA'
        par_f008 = 'SEMUA'
        params = {'f001': par_f001, 'f002': par_f002, 'f003': par_f003, 'f004': par_f004, 'f005': par_f005, 'f006': par_f006, 'f007': par_f007, 'f008': par_f008}
        url = _base_url_pmc + _service
        response = requests.post(url, params=params, headers=headers)
        data = json.loads(response.text)
        if (data["status"] == 1):
            if (data["data"]["graph"]):
                data_val = 0
            print(data_val)
            for data_graph in data["data"]["graph"]:
                if data_graph['f001'] == 'BONGKAR':
                    data_val = data_val + data_graph['f003']
            self.env['timbangan.vdata'].create({
               'bisnis_unit': "PMC",
               'tanggal': date,
               'bulan': month,
               'tahun': year,
               'val_timbangan': data_val
            })

        # IBPE
    def get_action_data_api_ibpe_days_v2(self, year, month, date):
        headers = {'Security': _security}
        par_f001 = date
        par_f002 = date
        par_f003 = 'IBPE'
        par_f004 = 'SEMUA'
        par_f005 = 'SEMUA'
        par_f006 = 'SEMUA'
        par_f007 = 'SEMUA'
        par_f008 = 'SEMUA'
        params = {'f001': par_f001, 'f002': par_f002, 'f003': par_f003, 'f004': par_f004, 'f005': par_f005, 'f006': par_f006, 'f007': par_f007, 'f008': par_f008}
        url = _base_url_pmc + _service
        response = requests.post(url, params=params, headers=headers)
        data = json.loads(response.text)
        if (data["status"] == 1):
            if (data["data"]["graph"]):
                data_val = 0
            for data_graph in data["data"]["graph"]:
                if data_graph['f001'] == 'BONGKAR':
                    data_val = data_val + data_graph['f003']
            self.env['timbangan.vdata'].create({
                'bisnis_unit': "IBPE",
                'tanggal': date,
                'bulan': month,
                'tahun': year,
                'val_timbangan': data_val
            })

    # ========== Get Current Month =============
    def get_data_bspc_current_month(self):
        curent_year = datetime.datetime.now().strftime("%Y")
        curent_month = datetime.datetime.now().strftime("%B")
        print("current Month")
        deldata = self.env['timbangan.vdata'].search(
            [('bulan', '=', curent_month), ('tahun', '=', curent_year), ('bisnis_unit', 'in', ['BSPC'])]).unlink()

        self.get_action_data_api_bspc_month_v2(curent_year, curent_month)
        # self.get_action_data_api_pmc_month(curent_year, curent_month)

        return {
            'name': 'View Timbangan',
            'view_mode': 'tree,kanban',
            'res_model': 'timbangan.vdata',
            'type': 'ir.actions.act_window',
            'context': "{'search_default_group_by_bisnis_unit': True, 'search_default_group_by_tanggal':True}",
        }

    def get_data_pmc_current_month(self):
        curent_year = datetime.datetime.now().strftime("%Y")
        curent_month = datetime.datetime.now().strftime("%B")
        print("current Month")
        deldata = self.env['timbangan.vdata'].search(
            [('bulan', '=', curent_month), ('tahun', '=', curent_year), ('bisnis_unit', 'in', ['PMC'])]).unlink()

        self.get_action_data_api_pmc_month_v2(curent_year, curent_month)

        return {
            'name': 'View Timbangan',
            'view_mode': 'tree,kanban',
            'res_model': 'timbangan.vdata',
            'type': 'ir.actions.act_window',
            'context': "{'search_default_group_by_bisnis_unit': True, 'search_default_group_by_tanggal':True}",
        }

    def get_data_ibpe_current_month(self):
        curent_year = datetime.datetime.now().strftime("%Y")
        curent_month = datetime.datetime.now().strftime("%B")
        print("current Month")
        deldata = self.env['timbangan.vdata'].search(
            [('bulan', '=', curent_month), ('tahun', '=', curent_year), ('bisnis_unit', 'in', ['IBPE'])]).unlink()

        self.get_action_data_api_ibpe_month_v2(curent_year, curent_month)

        return {
            'name': 'View Timbangan',
            'view_mode': 'tree,kanban',
            'res_model': 'timbangan.vdata',
            'type': 'ir.actions.act_window',
            'context': "{'search_default_group_by_bisnis_unit': True, 'search_default_group_by_tanggal':True}",
        }

    # ========== ##################### =============

    def get_data_bspc_before_current_month(self):
        curent_year = datetime.datetime.now().strftime("%Y")
        today = datetime.date.today()
        first = today.replace(day=1)
        last_month = first - datetime.timedelta(days=1)
        curent_before_month = last_month.strftime("%B")
        deldata = self.env['timbangan.vdata'].search(
            [('bulan', '=', curent_before_month), ('tahun', '=', curent_year), ('bisnis_unit', 'in', ['BSPC'])]).unlink()
        self.get_action_data_api_bspc_month_v2(curent_year, curent_before_month)

        return {
            'name': 'View Timbangan',
            'view_mode': 'tree,kanban',
            'res_model': 'timbangan.vdata',
            'type': 'ir.actions.act_window',
            'context': "{'search_default_group_by_bisnis_unit': True, 'search_default_group_by_tanggal':True}",
        }

    def get_data_pmc_before_current_month(self):
        curent_year = datetime.datetime.now().strftime("%Y")
        today = datetime.date.today()
        first = today.replace(day=1)
        last_month = first - datetime.timedelta(days=1)
        curent_before_month = last_month.strftime("%B")
        deldata = self.env['timbangan.vdata'].search(
            [('bulan', '=', curent_before_month), ('tahun', '=', curent_year), ('bisnis_unit', 'in', ['PMC'])]).unlink()
        self.get_action_data_api_pmc_month_v2(curent_year, curent_before_month)

        return {
            'name': 'View Timbangan',
            'view_mode': 'tree,kanban',
            'res_model': 'timbangan.vdata',
            'type': 'ir.actions.act_window',
            'context': "{'search_default_group_by_bisnis_unit': True, 'search_default_group_by_tanggal':True}",
        }

    def get_data_ibpe_before_current_month(self):
        curent_year = datetime.datetime.now().strftime("%Y")
        today = datetime.date.today()
        first = today.replace(day=1)
        last_month = first - datetime.timedelta(days=1)
        curent_before_month = last_month.strftime("%B")
        deldata = self.env['timbangan.vdata'].search(
            [('bulan', '=', curent_before_month), ('tahun', '=', curent_year), ('bisnis_unit', 'in', ['PMC'])]).unlink()
        self.get_action_data_api_ibpe_month_v2(curent_year, curent_before_month)

        return {
            'name': 'View Timbangan',
            'view_mode': 'tree,kanban',
            'res_model': 'timbangan.vdata',
            'type': 'ir.actions.act_window',
            'context': "{'search_default_group_by_bisnis_unit': True, 'search_default_group_by_tanggal':True}",
        }

    def get_action_data_api_bspc_month(self, year, month):
        headers = {'Security': _security}
        par_p001 = "refresh"
        par_f001 = "DAYS"
        par_f002 = year
        par_f003 = month
        params = {'p001': par_p001, 'f001': par_f001, 'f002': par_f002, 'f003': par_f003}
        url = _base_url_bspc + _service
        response = requests.post(url, params=params, headers=headers)
        data = json.loads(response.text)
        if (data["status"] == 1):
            if (data["data"]["x"]):
                dt = numpy.stack((numpy.array(data["data"]["x"]), numpy.array(data["data"]["val"])), axis=1)
            for list in dt:
                split_date = list[0].split("-")
                frm_data = split_date[2] + "-" + self.get_month_number(split_date[1]) + "-" + split_date[0]
                # if frm_data != date:
                #    continue
                self.env['timbangan.vdata'].create({
                    'bisnis_unit': "BSPC",
                    'tanggal': frm_data,
                    'bulan': split_date[1],
                    'tahun': split_date[2],
                    'val_timbangan': list[1]
                })
            else:
                print(data, "Response Oke (Empty)")
        else:
            print(data, "Response Error")

    def get_action_data_api_pmc_month(self, year, month):
        headers = {'Security': _security}
        par_p001 = "refresh"
        par_f001 = "DAYS"
        par_f002 = year
        par_f003 = month
        params = {'p001': par_p001, 'f001': par_f001, 'f002': par_f002, 'f003': par_f003}
        url = _base_url_pmc + _service
        response = requests.post(url, params=params, headers=headers)
        data = json.loads(response.text)
        data = json.loads(response.text)
        if (data["status"] == 1):
            if (data["data"]["x"]):
                dt = numpy.stack((numpy.array(data["data"]["x"]), numpy.array(data["data"]["val"])), axis=1)
                for list in dt:
                    split_date = list[0].split("-")
                    frm_data = split_date[2] + "-" + self.get_month_number(split_date[1]) + "-" + split_date[0]
                    # if frm_data != date:
                    #    continue
                    self.env['timbangan.vdata'].create({
                        'bisnis_unit': "PMC",
                        'tanggal': frm_data,
                        'bulan': split_date[1],
                        'tahun': split_date[2],
                        'val_timbangan': list[1]
                    })
            else:
                print(data, "Response Oke (Empty)")
        else:
            print(data, "Response Error")

    # versi 2
    # =====New Version API=====
    def get_action_data_api_bspc_month_v2(self, year, month):
        last_day = calendar.monthrange(int(year), int(self.get_month_number(month)))
        for r in range(1, int(last_day[1]+1)):
            date_r = year+'-'+self.get_month_number(month)+'-'+str(r)
            print(date_r,'date_r')
            self.get_action_data_api_bspc_days_v2(year, month, date_r)

    def get_action_data_api_pmc_month_v2(self, year, month):
        last_day = calendar.monthrange(int(year), int(self.get_month_number(month)))
        for r in range(1, int(last_day[1]+1)):
            n_date = r + 1
            date_r = year + '-' +self.get_month_number(month) + '-' + str(r)
            self.get_action_data_api_pmc_days_v2(year, month, date_r)

    def get_action_data_api_ibpe_month_v2(self, year, month):
        last_day = calendar.monthrange(int(year), int(self.get_month_number(month)))
        for r in range(1, int(last_day[1]+1)):
            n_date = r + 1
            date_r = year + '-' +self.get_month_number(month) + '-' + str(r)
            self.get_action_data_api_ibpe_days_v2(year, month, date_r)

    # ==========================================
    def get_data(self):
        curent_year = datetime.datetime.now().strftime("%Y")
        curent_month = datetime.datetime.now().strftime("%m")
        next_month = datetime.datetime.now() + relativedelta.relativedelta(months=1)
        next_month_number = next_month.strftime("%m")
        timbangan_data = self.env['timbangan.vdata'].search([('id', '!=', 0)])
        del_timbangan = timbangan_data.unlink()
        if del_timbangan:
            for y in _year:
                for m in _month:
                    # print(self.get_month_number(m), "M")
                    # print(curent_month, "current month")
                    # print(next_month_number, "next month")
                    # if m in ["November", "December"] and y == curent_year:
                    #    continue
                    if str(self.get_month_number(m)) == str(next_month_number) and y == curent_year:
                        break
                    # self.get_action_data_api_bspc(y, m)
                    self.get_action_data_api_pmc(y, m)

        return {
            'name': 'View Timbangan',
            'view_mode': 'tree,kanban',
            'res_model': 'timbangan.vdata',
            'type': 'ir.actions.act_window',
            'context': "{'search_default_group_by_bisnis_unit': True, 'search_default_group_by_tanggal':True}",
        }

    def get_action_data_api_bspc(self, year, month):
        headers = {'Security': _security}
        par_p001 = "refresh"
        par_f001 = "DAYS"
        par_f002 = year
        par_f003 = month
        params = {'p001': par_p001, 'f001': par_f001, 'f002': par_f002, 'f003': par_f003}
        url = _base_url_bspc + _service
        response = requests.post(url, params=params, headers=headers)
        data = json.loads(response.text)
        if (data["status"] == 1):
            if (data["data"]["x"]):
                dt = numpy.stack((numpy.array(data["data"]["x"]), numpy.array(data["data"]["val"])), axis=1)
                for list in dt:
                    split_date = list[0].split("-")
                    frm_data = split_date[2] + "-" + self.get_month_number(split_date[1]) + "-" + split_date[0]
                    self.env['timbangan.vdata'].create({
                        'bisnis_unit': "BSPC",
                        'tanggal': frm_data,
                        'bulan': split_date[1],
                        'tahun': split_date[2],
                        'val_timbangan': list[1]
                    })
            else:
                print(data, "Response Oke (Empty)")
        else:
            print(data, "Response Error")

    def get_action_data_api_pmc(self, year, month):
        headers = {'Security': _security}
        par_p001 = "refresh"
        par_f001 = "DAYS"
        par_f002 = year
        par_f003 = month
        params = {'p001': par_p001, 'f001': par_f001, 'f002': par_f002, 'f003': par_f003}
        url = _base_url_pmc + _service
        response = requests.post(url, params=params, headers=headers)
        data = json.loads(response.text)
        if (data["status"] == 1):
            if (data["data"]["x"]):
                dt = numpy.stack((numpy.array(data["data"]["x"]), numpy.array(data["data"]["val"])), axis=1)
                for list in dt:
                    split_date = list[0].split("-")
                    frm_data = split_date[2] + "-" + self.get_month_number(split_date[1]) + "-" + split_date[0]
                    self.env['timbangan.vdata'].create({
                        'bisnis_unit': 'PMC',
                        'tanggal': frm_data,
                        'bulan': split_date[1],
                        'tahun': split_date[2],
                        'val_timbangan': list[1]
                    })
            else:
                print(data, "Response Oke (Empty)")
        else:
            print(data, "Response Error")


class TimbanganData(models.Model):
   _name = 'timbangan.vdata'
   _rec_name = 'tanggal'
   _order = "bisnis_unit asc, tahun asc, bulan asc, tanggal asc"

   bisnis_unit = fields.Char(string="Bisnis Unit")
   tanggal = fields.Date(string="Tanggal")
   bulan = fields.Char(string="Bulan")
   tahun = fields.Char(string="Tahun")
   val_timbangan = fields.Float(string="Value")
   val_ton = fields.Float(string="Val (Ton)", compute="_get_val_ton", store=True)
   tipe_input = fields.Selection([('api', 'api'), ('import', 'import')], default='api', string='Tipe Input')
   # val_ton2 = fields.Float(string="Val2 (Ton)", compute="_get_val_ton", store=True)
   bu_company_id = fields.Many2one('res.company', string='Company', compute='_get_company', store=True)

   @api.depends("bisnis_unit")
   def _get_company(self):
      for res in self:
         if res.bisnis_unit:
            get_company = res.env['master.bisnis.unit'].search([('code', '=', res.bisnis_unit)])
            if get_company:
               res.bu_company_id = get_company.bu_company_id.id
         else:
            res.bu_company_id = 0
   @api.depends("val_timbangan")
   def _get_val_ton(self):
      for r in self:
         if r.val_timbangan > 0:
            r.val_ton = r.val_timbangan / 1000
            # r.val_ton2 = r.val_timbangan / 1000
         else:
            r.val_ton = 0
            # r.val_ton2 = 0

   def _get_test(self):
      print("TEST Scheduler")

   def write(self, values):
      for r in self:
         if r.tipe_input != 'import':
            raise ValidationError("Data Api tidak bisa di ubah")
         res = super(TimbanganData, r).write(values)
         return res

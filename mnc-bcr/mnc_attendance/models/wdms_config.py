from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

import requests
import json


class WDMSConfig(models.Model):
    _name = 'wdms.config'
    _description = "WDMS configuration"
    _rec_name = "username"

    username = fields.Char('Username', store=True, required=True)
    password = fields.Char('Password', store=True, required=True)
    ip_link = fields.Char('IP Link WDMS', required=True)

    token = fields.Text('Token', store=True)

    def action_get_token(self):
        url = _("%s/jwt-api-token-auth/") % (self.ip_link)
        # Parameter
        payload = json.dumps({
            'username': self.username,
            'password': self.password,
        })
        headers = {
          'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        # Result API
        data = json.loads(response.text)
        if response.status_code == 200:
            self.token = data['token']
            return
        else:
            raise ValidationError(_("Get Token Failed"))
        return

    def get_token(self):
        user_wdms = self.env['wdms.config'].search([('username', '!=', False), ('password', '!=', False), ('ip_link', '!=', False)], limit=1)
        if user_wdms:
            self.env["queue.job"].with_delay(
                priority=None,
                max_retries=None,
                channel=None,
                description="WDMS Token",
            ).get_token_wdms(user_wdms.id)


class AreaWDMS(models.Model):
    _name = 'wdms.area'
    _description = "WDMS Area"

    wdms_id = fields.Integer('WDMS ID', store=True)
    area_code = fields.Char('Area Code', store=True)
    area_name = fields.Char('Area Name', store=True)
    company_id = fields.Many2one('res.company', string="Companies", store=True)

    @api.model
    def action_get_area(self):
        config_id = self.env['wdms.config'].search([('token', '!=', False)], limit=1)
        wdms_area_obj = self.env['wdms.area']
        if config_id:
            url = _("%s/personnel/api/areas/") % (config_id.ip_link)
            auth = _("JWT %s") % (config_id.token)

            payload = {}
            headers = {
                'Content-Type': 'application/json',
                'Authorization': auth
            }

            response = requests.request("GET", url, headers=headers, data=payload)
            # Result API
            data = json.loads(response.text)
            if response.status_code == 200:
                for data in data['data']:
                    area_id = wdms_area_obj.search([('wdms_id', '=', data['id'])], limit=1)
                    if not area_id:
                        company_id = self.env['res.company'].search([('id', '=', data['company']['id'])], limit=1)
                        wdms_area_obj.create({
                            'wdms_id': data['id'],
                            'area_code': data['area_code'],
                            'area_name': data['area_name'],
                            'company_id': company_id.id
                        })
                return
            else:
                raise ValidationError(_("Get Data Failed"))
        return

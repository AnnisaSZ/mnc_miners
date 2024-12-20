import json
import base64

from odoo import http, SUPERUSER_ID, _
from odoo.http import request
from odoo.addons.web.controllers.main import Session

import secrets


def get_api_key(self):
    apikey = request.env['ir.config_parameter'].sudo().get_param('APIKEY')
    return apikey


def generate_token(length=32):
    # Menghasilkan token acak dengan panjang yang ditentukan
    return secrets.token_hex(length // 2)  # 1 byte = 2 karakter hex, jadi kita bagi 2


class UserBioLogin(http.Controller):

    @http.route('/api/account/bio/set_bio', type='json', auth='user', methods=['POST'], csrf=False)
    def InputBioDatas(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            if key == api_key:
                # if request.httprequest.data:
                #     parameter = json.loads(request.httprequest.data)
                user_id = request.env.user
                user_id.write({
                    'is_bio': True,
                    'bio_token': generate_token(),
                })
                result = {
                    "code": 2,
                    "data": {
                        'token': user_id.bio_token
                    },
                    "desc": "Set Token Bio Success"
                }
            else:
                result = {
                    "code": 3,
                    "desc": 'Failed to authentication'}
            return result

    # /web/session/authenticate
    @http.route('/web/session/bio', type='json', auth='none')
    def get_session_info_bio(self, values=None):
        if request.httprequest.data:
            parameter = json.loads(request.httprequest.data)
            # Check User with token
            user = request.env['res.users'].sudo().search([('bio_token', '=', parameter['params']['token']), ('is_bio', '=', True)], limit=1)
            if not user:
                return {"error": "Invalid token"}
            # Set session user berdasarkan user.id
            request.session.uid = user.id
            request.env.user = user  # Set user yang sedang aktif dalam sesi
            request.env.cr.commit()  # Commit untuk memastikan sesi disimpan
            # Session token user untuk auth jika sudah mendapatkan user
            request.session.session_token = user._compute_session_token(request.session.sid)
            companies = []
            for company in user.company_ids:
                companies.append([company.id, company.name])
            # Ambil session_id dari cookies
            return {
                'uid': user.id,
                'name': user.name,
                'email': user.login,
                'employee_data': {
                    'employee_id': user.mncei_employee_id.id,
                    'employee_name': user.mncei_employee_id.nama_lengkap,
                    'department_id': user.mncei_dept_id.id,
                },
                'user_companies': {
                    'current_companies': [user.company_id.id, user.company_id.name],
                    'allowed_companies': companies,
                }
            }

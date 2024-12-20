import json
import base64

from odoo import http, api, SUPERUSER_ID
from odoo.http import request


APIKEY = 'e308a8bc-a99e-4cc0-ad7a-cc1c96e7d147'


def check_email_domain(email):
    domain = 'mncgroup.com'
    try:
        # Memisahkan domain dari email
        email_domain = email.split('@')[1]
        # Memeriksa apakah domain email sesuai dengan domain yang diharapkan
        if email_domain == 'mncgroup.com':
            return True, domain
        else:
            return False, domain
    except IndexError:
        # Jika email tidak memiliki format yang benar
        return False, domain


def is_valid_base64(base64_string):
    try:
        base64_bytes = base64.b64decode(base64_string)
        reencoded_base64 = base64.b64encode(base64_bytes)
        return reencoded_base64 == base64_string.encode('utf-8')
    except Exception as e:
        return False


def get_api_key(self):
    apikey = request.env['ir.config_parameter'].sudo().get_param('APIKEY')
    return apikey


def QueryUpdateUser(user_id):
    query = '''
        UPDATE
            res_users
        SET
            active=False
        WHERE
            id=%s
    ''' % (user_id.id)
    request.env.cr.execute(query)
    fetch_data = request.env.cr.fetchall()
    return fetch_data


class MnceiMiners(http.Controller):
    # API untuk resgistration users
    @http.route('/api/account/check_users', type='json', auth="public")
    def check_user(self, email):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            env = request.env(user=SUPERUSER_ID, su=True)
            if key == api_key:
                domain_email, domain = check_email_domain(email)
                if domain_email:
                    datas = []
                    employee_id = env['mncei.employee'].sudo().search([('email', '=', email)], limit=1)
                    if employee_id:
                        user_id = env['res.users'].sudo().search([('login', '=', email)], limit=1)
                        user_archive_id = env['res.users'].sudo().search([('login', '=', email), ('active', '=', False)], limit=1)
                        if not user_id and not user_archive_id:
                            datas.append({
                                'employee_id': employee_id.id or 0,
                                'name': employee_id.nama_lengkap or "",
                                'email': employee_id.email or "",
                                'company_id': employee_id.company.id or 0,
                                'company_name': employee_id.company.name or "",
                                'department_id': employee_id.department.id or 0,
                                'department_name': employee_id.department.name or "",
                            })
                            result = {
                                "code": 2,
                                "desc": "Success",
                                "data": datas
                            }
                            return result
                        else:
                            result = {
                                "code": 3,
                                "desc": f"{email} already exits",
                                "data": [{
                                    'employee_id': employee_id.id,
                                    'user_id': user_id.id if user_id else user_archive_id.id
                                }]
                            }
                            return result
                    else:
                        result = {
                            "code": 3,
                            "desc": f"{email} is find in employee MNC Energy.",
                            "data": [{
                                'is_employee': False,
                                'user_id': False
                            }]
                        }
                        return result
                else:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": f"{email} is not part of domain {domain}."
                    }
                    return result

    @http.route('/api/account/registration_users', type='json', auth="public")
    def create_user(self, values=None):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            env = request.env(user=SUPERUSER_ID, su=True)
            api_key = get_api_key(self)
            if key == api_key:
                # Get Parameters
                if request.httprequest.data:
                    parameter = json.loads(request.httprequest.data)
                # Check employee
                if parameter['employee_id']:
                    datas = []
                    employee_id = env['mncei.employee'].sudo().browse(parameter['employee_id'])
                    bisnis_unit_id = env['master.bisnis.unit'].sudo().search([('bu_company_id', '=', employee_id.company.id)])
                    if employee_id:
                        # Check Image
                        if not parameter['photo']:
                            result = {
                                "code": 3,
                                "desc": "Please take your photo"}
                            return result
                        check_image = is_valid_base64(parameter['photo'])
                        if not check_image:
                            result = {
                                "code": 3,
                                "desc": "Please check your image"}
                            return result
                        name = f"{employee_id.nama_lengkap}_{employee_id.department.name}_{bisnis_unit_id.code}"
                        user_id = request.env['res.users'].sudo().create({
                            'name': name,
                            'login': employee_id.email,
                            'mncei_employee_id': employee_id.id,
                            'password': 'WelcomeToMNC123#',
                            'image_1920': parameter['photo'],
                            'active': True,
                            'is_login_mobile': True,
                            'bisnis_unit_id': bisnis_unit_id.id,
                            'company_id': employee_id.company.id,
                            'company_ids': [(6, 0, employee_id.company.ids)],
                        })
                        user_id.send_mail_psw()
                        datas.append({
                            'user_id': user_id.id
                        })
                        result = {
                            "code": 2,
                            "desc": "Success",
                            "data": datas
                        }
                        return result
                else:
                    result = {
                        "code": 3,
                        "data": [],
                        "desc": "Please input employee id"
                    }
                    return result
            else:
                result = {
                    "code": 4,
                    "desc": 'Access Denied'
                }
                return result

    # API Untuk Menonaktifkan account user
    @http.route('/api/account/nonaktif_users', type='json', auth="public")
    def archive_user(self, email, archive):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            api_key = get_api_key(self)
            # if key == APIKEY:
            if key == api_key:
                # Check User to delete
                user_id = request.env['res.users'].sudo().search([
                    ('login', '=', email)
                ])
                if user_id:
                    user_id.archive_user()
                    # Perform logout to terminate the current session
                    data = {'success': True, 'reason': 'Account User successfully non active'}
                else:
                    data = {'success': False, 'reason': 'Account User not found'}
                return data

import json
from odoo import http
from odoo.http import request


APIKEY = 'e308a8bc-a99e-4cc0-ad7a-cc1c96e7d147'

# Auth Superadmin
# username = 'andi.rahman@mncgroup.com'
# password = 'Welcome1234#'

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
    @http.route('/api/account/registration_users', type='json', auth="public")
    def create_user(self, username, email):
        if request.httprequest.headers.get('Api-key'):
            key = request.httprequest.headers.get('Api-key')
            env = request.env
            api_key = get_api_key(self)
            # if key == APIKEY:
            if key == api_key:
                query = '''
                    SELECT
                        id
                    FROM
                        res_users
                    WHERE
                        login=%s
                '''
                params = [email]
                env.cr.execute(query, params)
                result = env.cr.dictfetchall()
                company_id = request.env['res.company'].sudo().search([('name', '=', 'Bhakti Coal Resources')])
                # Created Users
                if not result:
                    user_id = request.env['res.users'].sudo().create({
                        'name': username,
                        'login': email,
                        'password': 'WelcomeToMNC123#',
                        'active': False,
                        'company_id': company_id.id,
                        'company_ids': [(6, 0, company_id.ids)],
                    })
                    user_id.send_mail_psw()
                    data = {'success': True, 'user_id': user_id.id}
                else:
                    data = {'success': False, 'reason': 'User already exists'}
                return data

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

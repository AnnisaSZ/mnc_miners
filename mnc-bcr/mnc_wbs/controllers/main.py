import logging
import werkzeug
from odoo.addons.auth_signup.models.res_users import SignupError



from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.web import Home
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.main import Home, SIGN_UP_REQUEST_PARAMS
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

#change default company odoobot and Portal User Template to mnc energy
SIGN_UP_REQUEST_PARAMS.update(['company','phone','other'])


class wbsLogin(AuthSignupHome):

    #override from auth_signup main.py
    @http.route('/wbs/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                # Send an account creation confirmation email
                User = request.env['res.users']
                user_sudo = User.sudo().search(
                    User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
                )
                template = request.env.ref('mnc_wbs.wbs_mail_template_user_signup_account_created', raise_if_not_found=False)
                if user_sudo and template:
                    template.sudo().send_mail(user_sudo.id, force_send=True)
                return request.redirect('/web/login')
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("Another user is already registered using this email address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")

        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
   
    # Replace method on auth_signup main.py
    def do_signup(self, qcontext):
        values = { key: qcontext.get(key) for key in ('login', 'name', 'password','company','phone','other') }
        password = values['password']
        user_id = request.env.user
        user_id._check_password(password)
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '')
        if lang in supported_lang_codes:
            values['lang'] = lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()
   
class Home(Home):

    @http.route()
    def index(self, *args, **kw):
        if request.session.uid and not request.env['res.users'].sudo().browse(request.session.uid).has_group('base.group_user'):
            link = 'wbs/home'
            return http.local_redirect(link, query=request.params, keep_hash=True)
        return super(Home, self).index(*args, **kw)
    
    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        if request.session.uid and not request.env['res.users'].sudo().browse(request.session.uid).has_group('base.group_user'):
            action_id = request.env.ref('mnc_wbs.list_report_view')
            view_id = request.env.ref('mnc_wbs.list_report_view_tree')
            link = 'wbs/home'
            return http.local_redirect(link, query=request.params, keep_hash=True)
        return super(Home, self).web_client(s_action, **kw)

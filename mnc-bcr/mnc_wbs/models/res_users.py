from odoo import fields, models, api, _
from odoo.addons.auth_signup.models.res_partner import SignupError, now
from ast import literal_eval
from odoo.tools.misc import ustr

class ResUsers(models.Model):
    _inherit = 'res.users'

    company = fields.Char(string='Department',)
    phone = fields.Char(string='Phone',)
    other = fields.Char(string='Other Company',)

    @api.model_create_multi
    def create(self, vals_list):
        users = super(ResUsers, self).create(vals_list)
        for user in users:
            # if partner is global we keep it that way
            if user.phone:
                user.partner_id.phone = user.phone
            if user.company or user.other:
                user.company_name = user.company if user.company else user.other
            if user.other and user.company == 'other':
                user.company_name = user.other
            user.partner_id.active = user.active
        return users

    #Replace function in auth_signup    
    def _create_user_from_template(self, values):
        template_user_id = literal_eval(self.env['ir.config_parameter'].sudo().get_param('base.template_portal_user_id', 'False'))
        template_user = self.browse(template_user_id)
        if not template_user.exists():
            raise ValueError(_('Signup: invalid template user'))
        if not values.get('login'):
            raise ValueError(_('Signup: no login given for new user'))
        if not values.get('partner_id') and not values.get('name'):
            raise ValueError(_('Signup: no name or partner given for new user'))

        # create a copy of the template user (attached to a specific partner_id if given)
        values['active'] = True
        values['email'] = values['login']
        values['login'] = 'wbs.'+values['login']

        try:
            with self.env.cr.savepoint():
                return template_user.with_context(no_reset_password=True).copy(values)
        except Exception as e:
            # copy may failed if asked login is not available.
            raise SignupError(ustr(e))

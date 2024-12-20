from odoo import fields, models, api, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.addons.auth_signup.models.res_partner import SignupError, now
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_login_mobile = fields.Boolean('Login Mobile')

    def send_mail_psw(self):
        template = self.env.ref('bcr_api_sh.email_template_send_notify_psw')
        template.send_mail(self.id, force_send=True, notif_layout='mail.mail_notification_light', email_values={'email_to': self.login})
        return True

    def archive_user(self):
        self.env.cr.execute(
            'UPDATE res_users SET active=False WHERE id=%s',
            (self.id,)
        )
        return

    # @Override
    # Dikarenakan template tidak bisa dirubah secara code, jadi dilakukan override untuk mengganti email template yang akan dikirim
    def action_reset_password(self):
        """ create signup token for each user, and send their signup url by email """
        print("====Action Reset====")
        if self.env.context.get('install_mode', False):
            return
        if self.filtered(lambda user: not user.active):
            raise UserError(_("You cannot perform this action on an archived user."))
        # prepare reset password signup
        create_mode = bool(self.env.context.get('create_user'))

        # no time limit for initial invitation, only for reset password
        expiration = False if create_mode else now(days=+1)

        self.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)

        # send email to users with their signup url
        template = False
        if create_mode:
            try:
                template = self.env.ref('base.set_password_email', raise_if_not_found=False)
            except ValueError:
                pass
        if not template:
            context = self._context
            print(context.get('mobile'))
            if context.get('mobile'):
                template = self.env.ref('bcr_api_sh.bcr_template_reset_psw')
            else:
                template = self.env.ref('auth_signup.reset_password_email')

        assert template._name == 'mail.template'

        template_values = {
            'email_to': '${object.email|safe}',
            'email_cc': False,
            'auto_delete': True,
            'partner_to': False,
            'scheduled_date': False,
        }
        template.write(template_values)

        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.", user.name))
            # TDE FIXME: make this template technical (qweb)
            with self.env.cr.savepoint():
                force_send = not(self.env.context.get('import_file', False))
                template.send_mail(user.id, force_send=force_send, raise_exception=True)
            _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)

from odoo import models, fields, api, _


class LogQontak(models.Model):
    _name = "qontak.logging"
    _rec_name = 'code'

    code = fields.Char('Code')
    recipient = fields.Char('Recipient')
    message = fields.Text('Message')

    def name_get(self):
        result = []
        for logging in self:
            name = f"[{logging.code}] {logging.recipient}"
            result.append((logging.id, name))
        return result

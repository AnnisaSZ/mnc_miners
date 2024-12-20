from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class MasterActivity(models.Model):
    _name = 'master.activity'
    _description = 'Master Activity'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    sub_activity_ids = fields.One2many('master.sub.activity', 'activity_id', string='Sub Activity')
    active = fields.Boolean(string='Active', default=True)


    @api.model
    def get_activity_by_code(self, code):
        result = False
        ma_id = self.env["master.activity"].search([('code', '=', code)], limit=1)

        if ma_id:
            result = ma_id.id
        else:
            raise UserError('Tidak ada Master Activity dengan kode [ %s ] \n\nsilakan hubungi administrator' %(code))

        return result

class MasterSubActivity(models.Model):
    _name = 'master.sub.activity'
    _description = 'Master Sub Activity'

    activity_id = fields.Many2one('master.activity', required=True, string='Activity')
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True, )
    active = fields.Boolean(string='Active', default=True)

from odoo import fields, api, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    #MASTER USER
    tipe_user = fields.Selection([('super_admin',       'Super Admin'),
                                  ('admin_mnc',         'Admin MNC'),
                                  ('spv',               'SPV data control'),
                                  ('admin_kontraktor',  'Admin kontraktor'),
                                  ('port_team',         'Port Team'),
                                  ('operator_timbangan','Operator Timbangan')
                                  ], string="Tipe User")
    bisnis_unit_id = fields.Many2one(comodel_name="master.bisnis.unit", string="Bisnis Unit")

    @api.model
    def get_default_bisnis_unit_id(self):
        result = False
        user = self.env["res.users"].browse(self._uid)
        if user:
            if self.env["master.bisnis.unit"].search([], limit=1):
                if user.bisnis_unit_id:
                    result = user.bisnis_unit_id.id
                else:
                    raise UserError('User anda harus memiliki Bisnis Unit, hubungi administrator')
            else:
                raise UserError('Bisnis Unit harus diinput di Master Bisnis Unit !')

        return result

    @api.model
    def get_default_bisnis_unit_seq_code(self):
        result = False
        user = self.env["res.users"].browse(self._uid)
        if user:
            if self.env["master.bisnis.unit"].search([], limit=1):
                if user.bisnis_unit_id:
                    if user.bisnis_unit_id:
                        result = user.bisnis_unit_id.seq_code
                    else:
                        raise UserError('User anda harus memiliki Seq Code pada Bisnis Unit, hubungi administrator')
                else:
                    raise UserError('User anda harus memiliki Bisnis Unit, hubungi administrator')
            else:
                raise UserError('Bisnis Unit harus diinput di Master Bisnis Unit !')

        return result

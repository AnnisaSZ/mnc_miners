from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date

import logging

_logger = logging.getLogger(__name__)


class MasterBisnisUnit(models.Model):
    _inherit = 'master.bisnis.unit'

    is_rom = fields.Boolean('Just INV PORT', store=True)


# class MasterSource(models.Model):
#     _inherit = 'master.source'

    # @api.model
    # def name_search(self, name, args=None, operator='ilike', limit=100):
    #     print("SSSSSSSSSSSSSSSSSSSSSSS")
    #     context = self._context
    #     print(context)
    #     args = args or []
    #     domain = []
    #     if context.get('opname'):
    #         sub_activity_id = self.env['master.sub.activity'].browse(context.get('sub_act'))
    #         print("====Sub Act====")
    #         print(sub_activity_id)
    #         if sub_activity_id.code == 'IN-PR':
    #             print("XXXXXXXXXXXXXXXX00")
    #             domain += [('source_group_id.num_sourcegroup', '=', 3)]
    #         rec = self.search(domain + args, limit=limit)
    #         return rec.name_get()
    #             return {'domain': {'source_id': [('source_group_id.num_sourcegroup', '=', 3)]}}
        #     if not context.get('temporary'):
        #         domain += [('company', 'in', context.get('company_ids')[0][2]), ('lokasi_kerja', '=', context.get('working_location')), ('state', '=', 'verified'), '|', ('nama_lengkap', operator, name), ('nip', operator, name)]
        #         print("Temporary")
        #     else:
        #         domain += [('state', '=', 'verified'), '|', ('nama_lengkap', operator, name), ('nip', operator, name)]
        #     rec = self.search(domain + args, limit=limit)
        #     return rec.name_get()
        # else:
        # res = super(MasterSource, self).name_search(name, args=args, operator=operator, limit=limit)
        # return res

from odoo import models, fields, api, _
# from odoo.exceptions import ValidationError
from itertools import groupby

import logging

_logger = logging.getLogger(__name__)


class PaymentContractor(models.Model):
    _name = "payment.contractor"
    _description = "Payment Contractor"

    contractor_id = fields.Many2one('fleet.sub.kontraktor', 'Contractor', store=True)
    activity_id = fields.Many2one('master.activity', 'Activity', store=True)
    date_from = fields.Date('Date From', store=True)
    date_to = fields.Date('Date To', store=True)
    line_ids = fields.One2many('payment.contractor.line', 'payment_id', string="Detail Operation")

    def action_get_shiftly(self):
        shiftly_obj = self.env['fleet.shiftly.prod']
        self.line_ids = False
        # check and get datas
        shiftly_ids = shiftly_obj.search_read([('date', '>=', self.date_from), ('date', '<=', self.date_to), ('date', '<=', self.date_to), ('sub_kontraktor_id', '=', self.contractor_id.id)], ['id', 'unit_equip_id', 'hm_total'])
        temp_shift = {}
        for record in shiftly_ids:
            key = record['unit_equip_id']
            if key[0] not in temp_shift:
                temp_shift[key[0]] = {}
                temp_shift[key[0]]['id'] = []
                temp_shift[key[0]]['hm_total'] = 0
            temp_shift[key[0]]['id'].append(record['id'])
            temp_shift[key[0]]['hm_total'] += record['hm_total']
        # create datas
        temp_lines = []
        for temp_id in temp_shift:
            temp_lines.append((0, 0, {
                'unit_equip_id': temp_id,
                'hm_total': temp_shift[temp_id]['hm_total']
            }))
        self.line_ids = temp_lines
        return


class PaymentContractorLine(models.Model):
    _name = "payment.contractor.line"
    _description = "Payment Contractor Line"

    payment_id = fields.Many2one('payment.contractor', 'Payment', store=True)
    unit_equip_id = fields.Many2one('fleet.equipment.unit', string='Unit Equipment', store=True)
    hm_total = fields.Float('HM Total', store=True)

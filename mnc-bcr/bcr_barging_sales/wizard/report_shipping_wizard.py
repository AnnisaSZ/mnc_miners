# -*- coding: utf-8 -*-
from odoo import  fields, models, _
from odoo.exceptions import ValidationError, UserError



class ReportShippingSalesWiz(models.TransientModel):
    """MNC Report Shipping Wizard."""
    _name = "reports.shipping.wizard"
    _description = "MNC Report Shipping Wizard"

    barge_lineup_id = fields.Many2one(
        'barge.lineup',
        string='Barge Lineup'
    )

    def button_print_si(self):
        if not self.barge_lineup_id.barge_detail_ids.no_si:
            raise ValidationError(_("No. SI cannot be blank!"))
        return self.env.ref('bcr_barging_sales.action_print_si').report_action(self)
    
    def button_print_spk(self):
        if not self.barge_lineup_id.barge_detail_ids.no_spk:
            raise ValidationError(_("No. SPK cannot be blank!"))
        return self.env.ref('bcr_barging_sales.action_print_spk').report_action(self)
    
    def button_print_skab(self):
        if not self.barge_lineup_id.barge_detail_ids.no_skab:
            raise ValidationError(_("No. SKAB cannot be blank!"))
        return self.env.ref('bcr_barging_sales.action_print_skab').report_action(self)
    
    def button_print_spb(self):
        if not self.barge_lineup_id.barge_detail_ids.no_spb:
            raise ValidationError(_("No. SPB cannot be blank!"))
        return self.env.ref('bcr_barging_sales.action_print_spb').report_action(self)
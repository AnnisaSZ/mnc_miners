from odoo import fields, models, api, _
from odoo.exceptions import AccessError
from collections import defaultdict
from datetime import datetime
import base64



ROMAN_NUMBER = {
    '1': 'I',
    '2': 'II',
    '3': 'III',
    '4': 'IV',
    '5': 'V',
    '6': 'VI',
    '7': 'VII',
    '8': 'VIII',
    '9': 'IX',
    '10': 'X',
    '11': 'XI',
    '12': 'XII',
}

COMPANY_CODE = {
    'Bhumi Sriwijaya Perdana Coal': 'BSPC',
    'Bhakti Coal Resources': 'BCR',
    'Indonesia Batu Prima Energi': 'IBPE',
    'Putra Muba Coal': 'PMC',
    'Arthaco Prima Energy': 'APE',
    'Global Maintenance Facility': 'GMF',
    'Indonesia Air Transport': 'IAT',
    'MNC Energy Investments': 'MNCEI',
    'MNC Infrastruktur Utama': 'INFRA',
    'Suma Sarana': 'SUMA',
}


class Attachment(models.Model):
    _inherit = 'ir.attachment'
    _order = 'id'
    
    attach_rel = fields.Many2many('wbs.report', 'attachment', 'attachment_id', 'document_id', string = "Attachment")

    # Override module from base ir.attachment
    @api.model
    def check(self, mode, values=None):
        """ Restricts the access to an ir.attachment, according to referred mode """
        if self.env.is_superuser():
            return True
        # Always require an internal user (aka, employee) to access to a attachment
        if not self.env.user.has_group('mnc_energy_information.group_ann_user'):
            if not (self.env.is_admin() or self.env.user.has_group('base.group_user') or self.env.user.has_group('base.group_portal')):
                raise AccessError(_("Sorry, you are not allowed to access this document."))
        # collect the records to check (by model)
        model_ids = defaultdict(set)            # {model_name: set(ids)}
        if self:
            # DLE P173: `test_01_portal_attachment`
            self.env['ir.attachment'].flush(['res_model', 'res_id', 'create_uid', 'public', 'res_field'])
            self._cr.execute('SELECT res_model, res_id, create_uid, public, res_field FROM ir_attachment WHERE id IN %s', [tuple(self.ids)])
            for res_model, res_id, create_uid, public, res_field in self._cr.fetchall():
                if public:
                    continue
                # elif not self.env.user.has_group('mnc_energy_information.group_ann_user'):
                #     if not self.env.is_system() and (res_field or (not res_id and create_uid != self.env.uid)):
                #         raise AccessError(_("Sorry, you are not allowed to access this document."))
                elif not (res_model and res_id):
                    continue
                model_ids[res_model].add(res_id)
        if values and values.get('res_model') and values.get('res_id'):
            model_ids[values['res_model']].add(values['res_id'])

        # check access rights on the records
        for res_model, res_ids in model_ids.items():
            # ignore attachments that are not attached to a resource anymore
            # when checking access rights (resource was deleted but attachment
            # was not)
            if res_model not in self.env:
                continue
            if res_model == 'res.users' and len(res_ids) == 1 and self.env.uid == list(res_ids)[0]:
                # by default a user cannot write on itself, despite the list of writeable fields
                # e.g. in the case of a user inserting an image into his image signature
                # we need to bypass this check which would needlessly throw us away
                continue
            records = self.env[res_model].browse(res_ids).exists()
            # For related models, check if we can write to the model, as unlinking
            # and creating attachments can be seen as an update to the model
            access_mode = 'write' if mode in ('create', 'unlink') else mode
            records.check_access_rights(access_mode)
            records.check_access_rule(access_mode)

class WbsReport(models.Model):
    _name = 'wbs.report'
    _description = 'WBS Report User'
    _order = 'id desc'

    name = fields.Char('Report Number', default="New", store=True, readonly=True)
    title = fields.Char('Report Title', default="New", store=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Business Unit', store=True,copy=False, readonly=True)
    start_date = fields.Date('Start Date', store=True, readonly=True)
    end_date = fields.Date('End Date', store=True, readonly=True)
    start_date_audit = fields.Date('Start Date Audit', store=True, readonly=True)
    end_date_audit = fields.Date('End Date Audit', store=True, readonly=True)
    description = fields.Text('Description', store=True, readonly=True)
    state = fields.Selection([
        ('Draft', 'Draft'),
        ('Submit', 'Process'),
        ('Close', 'Close'),
    ], string='Status', default='Draft', store=True, required=True, copy=False, track_visibility='onchange', readonly=True)

    attachment=fields.Many2many('ir.attachment', 'attach_rel', 'doc_id', 'attach_id', string="Attachment", help='You can upload your document', copy=False, readonly=True)

    # Profile User
    user_name = fields.Char(related="create_uid.name", string="Full Name")
    user_phone = fields.Char(related="create_uid.partner_id.phone", string="Phone Number")
    user_email = fields.Char(related="create_uid.login", string="Email")
    user_company = fields.Char(related="create_uid.company_name", string="Company")

    list_dir_report_ids = fields.One2many('wbs.report.bod', 'list_report_id', string='Report Employee', copy=False)


    def submit(self):
        name = self._get_sequence()
        bod = self.sudo().env['wbs.report.bod']

        self.write({'state': 'Submit',
                    'name': name,
                    })
        report_bod_id = bod.create(self.prepare_director_list())
        attch_ids = []
        Attachment = self.env['ir.attachment']
        for files in self.attachment:
            if files and files.name != '':
                attachment_id = Attachment.create({
                    'name': files.name,
                    'type': 'binary',
                    'datas': files.datas,
                    'res_model': 'wbs.report.bod',
                    'res_id': report_bod_id.id
                })
                attch_ids.append(attachment_id.id)
        report_bod_id.update({
            'attachment_ids': [(6, 0, attch_ids)],
        })
        report_bod_id.send_notif_new_report()       

    def _get_sequence(self):
        sequence = self.sudo().env['ir.sequence'].next_by_code('wbs.sequence')
        code_month = ROMAN_NUMBER[str(datetime.now().month)]
        company = self.sudo().env['res.company'].search([('id','=',self.company_id.id)])
        company = COMPANY_CODE[company.name]
        sequence = sequence.replace('MONTH', code_month)
        sequence = sequence.replace('COMPANY_CODE', company)

        return sequence or '/'
    
    def prepare_director_list(self):
        vals = ({
            'list_report_id': self.id,
            'name': self.name,
            'title': self.title,
            'company_id': self.company_id.id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'description': self.description,
        })
        return vals
    
    



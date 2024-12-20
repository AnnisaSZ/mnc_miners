from odoo import models, fields, _

class ModuleReminder(models.Model):
    _name = 'module.reminder'
    _description = 'Module Reminder Form'
    _order = 'id desc'
    _rec_name = 'model_id'

    name = fields.Char('name')
    model_id = fields.Many2one('ir.model', string="Modul", required=True, ondelete='cascade')
    fields_id = fields.Many2one('ir.model.fields', string="Field", required=True, ondelete='cascade')
    interval_time = fields.Selection([
        ('days', 'Daily'),
        ('weeks', 'Weekly'),
        ('months', 'Monthly'),
        ('years', 'Yearly'),
    ], string='Reminder Interval', default='days', store=True, required=True, copy=False)

    user_ids = fields.Many2many('res.users', string='User', store=True, required=True, copy=False)
    execution_date = fields.Datetime('Execution Date', required=True)

    status = fields.Selection([
        ('active', 'Active'),
        ('non_active', 'Non Active'),
    ], string='Status', default='non_active', store=True, required=True, copy=False)

    def activate(self):
        for rec in self:
            rec.write({'status':'active'})
            rec.create_cron_job()

    def deactivate(self):
        for rec in self:
            existing_cron = rec.get_cron_job()
            if existing_cron:
                existing_cron.write({'active':False})
            rec.write({'status':'non_active'})

    def check_reminder(self):
        id = self.env.context.get('reminder_id')
        active_id = self.search([('id','=', id)])
        res_search = self.env[active_id.model_id.model].search([])
        print("\n\n\n res_search", res_search)
        return True
    
    def get_cron_job(self):
        res = self.env['ir.cron'].search([('name', '=', 'Reminder ' + self.model_id.name)])
        return res

    def create_cron_job(self):
        existing_cron = self.get_cron_job()
        interval_time = self.interval_time
        interval_number = 1

        if interval_time == 'years':
            interval_time = 'months'
            interval_number = 12
        
        cron_vals = {
            'name': 'Reminder ' + self.model_id.name,
            'model_id': self.env.ref('mnc_reminder.model_module_reminder').id,
            'state': 'code',
            'user_id': self.env.ref('base.user_admin').id,
            'interval_number': interval_number,
            'interval_type': interval_time,
            'nextcall': self.execution_date,
            'numbercall': -1,
            'code': 'model.with_context(reminder_id='+ str(self.id) +').check_reminder()',
        }
        if existing_cron:
            cron_job = existing_cron.write(cron_vals)
        else:
            cron_job = self.env['ir.cron'].create(cron_vals)
        return cron_job

class IrModel(models.Model):
    _inherit = 'ir.model'

    notify_reminder_ids = fields.One2many('module.reminder', 'model_id')


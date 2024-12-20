from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.http import request


class MnceiTicketType(models.Model):
    _name = 'mncei.ticket.type'
    _description = 'MNCEI Ticket Type'

    def _categ_ids_domain(self):
        return [('dept_id', '=', self.env.context.get('department_id'))]

    name = fields.Char(
        string='Type Name', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Aktif'),
            ('nonaktif', 'Non Aktif')
        ], default='aktif', store=True, string='Status', required=True)
    categ_ids = fields.One2many(
        'mncei.ticket.category',
        'type_id',
        string='Category Ticket', store=True, domain=_categ_ids_domain
    )
    duration_auto_solve = fields.Integer(
        string='Duration Auto Solve(Hours)', store=True, default=1
    )


class MnceiTicketCategory(models.Model):
    _name = 'mncei.ticket.category'
    _description = 'MNCEI Ticket Category'

    name = fields.Char(
        string='Category Name', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Aktif'),
            ('nonaktif', 'Non Aktif')
        ], default='aktif', store=True, string='Status', required=True)
    type_id = fields.Many2one(
        'mncei.ticket.type',
        string='Request Type', store=True, required=True
    )
    uid = fields.Many2one(
        'res.users',
        string='User', default=lambda self: self.env.user, store=True
    )
    dept_uid = fields.Many2one(
        'mncei.department',
        string='User', related='uid.mncei_dept_id', store=True
    )
    dept_id = fields.Many2one(
        'mncei.department',
        string='Department', store=True, tracking=True, required=True, domain="[('state', '=', 'active'), ('id', '=', dept_uid)]"
    )
    duration_auto_solve = fields.Integer(
        string='Duration Auto Solve(Hours)', store=True, default=1, required=True
    )


    # @api.model
    # def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
    #     print("XXXXXXXXXXXXXXXXXXXXXXX")
    #     print(domain)
    #     print(fields)
    #     # self._check_referral_fields_access(fields)
    #     return super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    # def read(self, fields=None, load='_classic_read'):
    #     records = super(MnceiTicketCategory, self).read(fields, load)
    #     print("SSSSSSSSSSSSSSSSSSSSSSSSS")
    #     print(records)
    #     print(fields)
    #     context = self.env.context
    #     print(context)
    #     print(self._context)
    #     print(records)
    #     category = []
    #     for rec in records:
    #         print(rec)
    #         print(rec.get('dept_id')[0])
    #         if self.env.user.mncei_dept_id.id == rec.get('dept_id')[0]:
    #             print()
    #             print(rec)
    #             category.append(rec)
    #     # context.update({''})
    #     print("======Result=====")
    #     print(records)
    #     print("======Category=====")
    #     print(category)
    #     # records = []
    #     return records


class MnceiTicketState(models.Model):
    _name = 'mncei.ticket.state'
    _description = 'MNCEI Ticket Status'

    sequence = fields.Integer('Sequence', default=1, store=True)
    name = fields.Char(
        string='Status Name', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Aktif'),
            ('nonaktif', 'Non Aktif')
        ], default='aktif', store=True, string='Status', required=True)
    is_draft = fields.Boolean('Is Draft', store=True)
    is_finish = fields.Boolean('Is Finish', store=True)
    is_solved = fields.Boolean('Is Solved', store=True)


# class IrHttp(models.AbstractModel):
#     _inherit = 'ir.http'

#     def session_info(self):
#         user = request.env.user
#         result = super(IrHttp, self).session_info()
#         print("================Ticket==========")
#         print(result.get('user_context'))
#         print(user)
#         result.update({
#             'department_id': user.mncei_dept_id.id or False
#         })
#         result.get('user_context').update({
#             'department_id': user.mncei_dept_id.id or False
#         })
#         return result

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class RiskLevel(models.Model):
    _name = 'risk.level'
    _description = 'Risk Level'
    _rec_name = 'risk_level'

    risk_level = fields.Char(
        string='Risk Level', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Active'),
            ('nonaktif', 'Non Active')
        ], default='aktif', store=True, string='Status', required=True
    )


class RiskControl(models.Model):
    _name = 'risk.control'
    _description = 'Risk Control'
    _rec_name = 'risk_control'

    risk_control = fields.Char(
        string='Risk Control', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Active'),
            ('nonaktif', 'Non Active')
        ], default='aktif', store=True, string='Status', required=True
    )


class PenalyPoint(models.Model):
    _name = 'penalty.point'
    _description = 'Penalty'
    _rec_name = 'penalty'

    penalty = fields.Char(
        string='Penalty', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Active'),
            ('nonaktif', 'Non Active')
        ], default='aktif', store=True, string='Status', required=True
    )


class LocationPoint(models.Model):
    _name = 'location.point'
    _description = 'Location'
    _rec_name = 'location'

    location = fields.Char(
        string='Location', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Active'),
            ('nonaktif', 'Non Active')
        ], default='aktif', store=True, string='Status', required=True
    )


class ActivityHazard(models.Model):
    _name = 'activity.hazard'
    _description = 'Activity'
    _rec_name = 'activity'

    activity = fields.Char(
        string='Activity', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Active'),
            ('nonaktif', 'Non Active')
        ], default='aktif', store=True, string='Status', required=True
    )


class CategoryHazard(models.Model):
    _name = 'category.hazard'
    _description = 'Category'
    _rec_name = 'category'

    code = fields.Char('Code', store=True, required=True)
    category = fields.Char(
        string='Category', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Active'),
            ('nonaktif', 'Non Active')
        ], default='aktif', store=True, string='Status', required=True
    )


class CategoryDanger(models.Model):
    _name = 'category.danger'
    _description = 'Category Danger'
    _rec_name = 'category_danger'

    category_danger = fields.Char(
        string='Category Danger', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Active'),
            ('nonaktif', 'Non Active')
        ], default='aktif', store=True, string='Status', required=True
    )


class DepartmentHse(models.Model):
    _name = 'department.hse'
    _description = 'Department HSE'

    name = fields.Char(
        string='Department', store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Active'),
            ('nonaktif', 'Non Active')
        ], default='aktif', store=True, string='Status', required=True
    )


class DepartmentPic(models.Model):
    _name = 'department.pic'
    _description = 'PIC Department'
    # _rec_name = 'pic_id'

    def _company_ids_domain(self):
        return [('id', 'in', self.env.user.company_ids.ids)]

    department_id = fields.Many2one(
        'department.hse',
        string='Department', store=True, required=True
    )
    pic_id = fields.Many2one(
        'res.users',
        string='PIC ', store=True
    )
    company_id = fields.Many2one('res.company', 'Company', store=True, domain=_company_ids_domain, required=True)
    pic_ids = fields.Many2many(
        'res.users',
        string='PIC ', domain="[('company_ids', 'in', company_id)]", store=True, required=True
    )
    status = fields.Selection(
        [
            ('aktif', 'Active'),
            ('nonaktif', 'Non Active')
        ], default='aktif', store=True, string='Status', required=True
    )
    child_ids = fields.One2many(
        'child.pic',
        'parent_id',
        string='Teams', store=True
    )

    def name_get(self):
        result = []
        for pic_dept in self:
            name_list = []
            if pic_dept.pic_ids:
                for pic_id in pic_dept.pic_ids:
                    name_list.append(pic_id.name)
            name = _("PIC : (%s)") % (', '.join(name_list))
            result.append((pic_dept.id, name))
        return result


class ChildPic(models.Model):
    _name = 'child.pic'
    _description = 'Teams Department'
    _rec_name = 'child_uid'

    parent_id = fields.Many2one(
        'department.pic',
        string='PIC Department', ondelete='cascade'
    )
    child_uid = fields.Many2one(
        'res.users', string='Teams Name',
    )
    status = fields.Selection(
        [
            ('aktif', 'Active'),
            ('nonaktif', 'Non Active')
        ], default='aktif', store=True, string='Status', required=True
    )

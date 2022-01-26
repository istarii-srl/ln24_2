from odoo import fields, api, models

class Resource(models.Model):
    _name = "resource.resource"
    _inherit = "resource.resource"

    employee_single_id = fields.Many2one(string="Employé", comodel_name="hr.employee", compute="_compute_ref_employee")


    @api.depends("employee_id")
    def _compute_ref_employee(self):
        for resource in self:
            if len(resource.employee_id) > 0:
                resource.employee_single_id = resource.employee_id[0]
            else:
                resource.employee_single_id = False
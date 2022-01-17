from odoo import fields, api, models

class Employee(models.Model):
    _inherit = "hr.employee"

    ln_employee_type_id = fields.Many2one(string="Type de l'employé ", comodel_name="ln.employee.type")

    def _planning_confirm_get_url(self, planning):
        result = {}
        for employee in self:
            result[employee.id] = '/confirm/%s/%s' % (planning.access_token, employee.employee_token)
        return result

class EmployeeType(models.Model):
    _name = "ln.employee.type"
    _description = "Type d'employé"

    name = fields.Char(string="Type d'employé")
from lxml.builder import E
from odoo import fields, api, models

class Attendance(models.Model):
    _name = "hr.attendance"
    _inherit = "hr.attendance"

    done_hours = fields.Float(string="Heures prestées")
    attendance_hours = fields.Float(string="Temps de travail")
    rest_hours = fields.Float(string="Temps de pause")
    worked_hours = fields.Float(string="Heures légales", readonly=False)
    rule_name = fields.Char(string="Nom de la règle appliquée", readonly=True)


    def apply_rules(self):
        for attendance in self:
            try:
                rules = self.env["ln.attendance.rule"].search([])
                rules = sorted(rules, key= lambda x: x.sequence)
                for rule in rules:
                    if rule.does_rule_match_attendance(attendance):
                        hours = rule.get_legal_hours(attendance)
                        attendance.rule_name = rule.name
                        attendance.worked_hours = hours
                        break
            except:
                pass
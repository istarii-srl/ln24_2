from lxml.builder import E
from odoo import fields, api, models

class Attendance(models.Model):
    _name = "hr.attendance"
    _inherit = "hr.attendance"

    done_hours = fields.Float(string="Heures prestées", compute="_compute_done_hours", store=True)
    attendance_hours = fields.Float(string="Temps de travail", compute="_compute_worked_hours")

    rest_hours = fields.Float(string="Temps de pause")
    worked_hours = fields.Float(string="Heures légales", readonly=False)
    rule_id = fields.Many2one(string="Règle", comodel_name="ln.attendance.rule")
    rule_name = fields.Char(string="Nom de la règle appliquée", readonly=True, related="rule_id.name")

    @api.model
    def create(self, vals):
        obj = super(Attendance, self).create(vals)
        if not obj.rule_id:
            obj.worked_hours = obj.done_hours
        return obj

    @api.onchange('done_hours')
    def on_done_hours_changed(self):
        for attendance in self:
            if not attendance.rule_id:
                attendance.worked_hours = attendance.done_hours

    @api.depends('worked_hours','rest_hours')
    def _compute_done_hours(self):
        for attendance in self:
            attendance.done_hours = attendance.worked_hours - attendance.rest_hours

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                delta = attendance.check_out - attendance.check_in
                attendance.attendance_hours = delta.total_seconds() / 3600.0
            else:
                attendance.attendance_hours = False

    def apply_rules(self):
        for attendance in self:
            try:
                rules = self.env["ln.attendance.rule"].search([])
                rules = sorted(rules, key= lambda x: x.sequence)
                for rule in rules:
                    if rule.does_rule_match_attendance(attendance):
                        hours = rule.get_legal_hours(attendance)
                        attendance.rule_id = rule
                        attendance.rule_name = rule.name
                        attendance.worked_hours = hours
                        break
            except:
                pass
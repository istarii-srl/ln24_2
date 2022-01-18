from odoo import fields, api, models
import logging
import datetime

_logger = logging.getLogger(__name__)

class AttendanceRule(models.Model):
    _name = "ln.attendance.rule"
    _description = "Règle de calcul des heures prestées pour les heures supplémentaires"

    name = fields.Char(string="Nom")
    matching_type = fields.Selection(string="Matching condition type", selection=[("any", "Any"), ("all", "All")], default="all", required=True)

    employee_type_ids = fields.Many2many(string="Type d'employé", comodel_name="ln.employee.type")
    day_ids = fields.Many2many(string="Jour de la semaine", comodel_name="ln.day")
    activity_holidays = fields.Selection(string="Actifs les jours fériés", selection=[('only', "Seulement les jours fériés"), ("never", "Pas les jours fériés"), ("both", "Jours fériés et jours normaux")], default="never", required=True)
    active = fields.Boolean(string="Actif", default=True)
    sequence = fields.Integer(string="Pos.")

    condition_ids = fields.One2many(string="Conditions", comodel_name="ln.attendance.condition", inverse_name="rule_id")


    def get_deduct_condi_id(self, attendance):
        for rule in self:
            res = None
            for condi in rule.condition_ids:
                if condi.should_deduct_rest_hours(attendance):
                    return condi
                elif condi.could_deduct_rest_hours(attendance):
                    res = condi
            if res:
                return res
            else:
                return rule.condition_ids[0]
            

    def get_legal_hours(self, attendance):
        for rule in self:
            res = 0
            deduct_condi_id = rule.get_deduct_condi_id(attendance)
            for condi in rule.condition_ids:
                res += condi.get_legal_hours(attendance, deduct_condi_id.id)
            return res

    def check_employee_match(self, employee):
        for rule in self:
            if employee.ln_employee_type_id in rule.employee_type_ids:
                return True
            else:
                return False
        
    def check_day_match(self, in_time, out_time):
        for rule in self:
            for allowed_day in rule.day_ids:
                if allowed_day.include_all or in_time.weekday()+1 == allowed_day.day_position:
                    return True
            return False
    
    def check_holiday_match(self, in_time, out_time):
        for rule in self:
            holidays = self.env["resource.calendar.leaves"].search([])
            is_holiday = False
            for holiday in holidays:
                if holiday.date_from.date() == in_time.date() or holiday.date_to.date() == in_time.date():
                    is_holiday = True
            if rule.activity_holidays == "only" and is_holiday:
                return True
            elif rule.activity_holidays == "never" and not is_holiday:
                return True
            elif rule.activity_holidays =="both":
                return True
            else:
                return False

    def does_rule_match_attendance(self, attendance):
        for rule in self:
            employee_match = rule.check_employee_match(attendance.employee_id)
            day_match = rule.check_day_match(attendance.check_in, attendance.check_out)
            holiday_match = rule.check_holiday_match(attendance.check_in, attendance.check_out)
            if rule.matching_type == "any":
                return employee_match or day_match or holiday_match
            else:
                return employee_match and day_match and holiday_match
            


class AttendanceCondition(models.Model):
    _name = "ln.attendance.condition"
    _description = "Exprime un calcul d'une règle"

    name = fields.Char(string="Name", compute="_compute_name")
    frame_id = fields.Many2one(string="Plage horaire", comodel_name="ln.attendance.frame", required=True)
    value_type = fields.Selection(string="Type de valeur", selection=[("percentage", "Pourcentage"), ("fixed", "Valeur fixe"), ("fixed_percentage", ("Fixe * pourcentage"))], default="percentage", required=True)
    percentage = fields.Float(string="Pourcentage", default=1.0)
    fixed_value = fields.Float(string="Valeur fixe", default=0)
    rule_id = fields.Many2one(string="Règle", comodel_name="ln.attendance.rule", required=True)
    should_deduct_rest_time_here = fields.Boolean(string="Déduire les heures de midi ici", default=False)

    sequence = fields.Integer(string="Pos.")
     

    @api.depends('frame_id', 'value_type', 'percentage', 'fixed_value')
    def _compute_name(self):
        for condi in self:
            if not condi.frame_id:
                condi.name = "/"
            else:
                text = ""
                text += condi.frame_id.name + " : "
                if condi.value_type == "fixed_percentage":
                    text += str(condi.percentage*100)
                    text += "% *"
                    text += str(condi.fixed_value)
                elif condi.value_type == "percentage":
                    text += str(condi.percentage*100)
                    text += "%"
                else:
                    text += str(condi.fixed_valued)

                condi.name = text


    def could_deduct_rest_hours(self, attendance):
        for condi in self:
            hours = condi.frame_id.get_overlapping_hours(attendance.check_in, attendance.check_out)
            return hours >= attendance.rest_hours

    def should_deduct_rest_hours(self, attendance):
        for condi in self:
            hours = condi.frame_id.get_overlapping_hours(attendance.check_in, attendance.check_out)
            return hours >= attendance.rest_hours and condi.should_deduct_rest_time_here

    def get_legal_hours(self, attendance, condi_id):
        for condi in self:
            hours = condi.frame_id.get_overlapping_hours(attendance.check_in, attendance.check_out)
            if hours > 0:
                if condi_id == condi.id:
                    hours = hours - attendance.rest_hours
                if condi.value_type == "fixed":
                    return condi.fixed_value
                elif condi.value_type == "fixed_percentage":
                    return condi.fixed_value * condi.percentage
                else:
                    return condi.percentage * hours
            else:
                return 0


class AttendanceFrame(models.Model):
    _name = "ln.attendance.frame"
    _description = "Plage horaire"

    name = fields.Char(string="Nom", required=True)
    start_hour = fields.Integer(string="Heure de début")
    start_minute = fields.Integer(string="Minute de début")
    end_hour = fields.Integer(string="Heure de fin")
    end_minute = fields.Integer(string="Minute de fin")
    all_day = fields.Boolean(string="Toute la journée", default=False)

    def get_overlapping_hours(self, check_in, check_out):
        for frame in self:
            frame_start = datetime.datetime(check_in.year, check_in.month, check_in.day, frame.start_hour, frame.start_minute)
            frame_end = datetime.datetime(check_out.year, check_out.month, check_out.day, frame.end_hour, frame.end_minute)
            if frame.all_day:
                return (check_out - check_in).total_seconds() / 60.0 / 60.0 
            if check_in >= frame_end:
                return 0.0
            elif check_in <= frame_start:
                if check_out >= frame_end:
                    return (frame_end - frame_start).total_seconds() / 60.0 / 60.0
                else:
                    return (check_out - frame_start).total_seconds() / 60.0 / 60.0
            else:
                if check_out >= frame_end:
                    return (frame_end - check_in).total_seconds() / 60.0 / 60.0
                else:
                    return (check_out - check_in).total_seconds() / 60.0 / 60.0





    

    
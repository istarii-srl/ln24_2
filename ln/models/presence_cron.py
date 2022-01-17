from odoo import fields, api, models
import datetime
import logging
_logger = logging.getLogger(__name__)



class PresenceCron(models.Model):
    _name = "ln.presence.cron"
    _description = "Cron job to sync planning and presence modules"

    def run_cron(self):
        _logger.info("Presence cron")
        today_start = datetime.datetime.now().replace(hour=0, minute=0, second=3)
        today_end = datetime.datetime.now().replace(hour=0, minute=0, second=2) + datetime.timedelta(days=1)
        slots = self.env["planning.slot"].search([("end_datetime", "<=", today_end), ("end_datetime", ">=", today_start), ('state', "=", "published")])
        _logger.info("number of slots")
        _logger.info(str(len(slots)))
        for slot in slots:
            _logger.info("in slot")
            if slot.employee_id and not slot.has_synced:
                try:
                    if slot.start_datetime.date() != slot.end_datetime.date():
                        attendance = self.env["hr.attendance"].create({
                            "check_in": slot.start_datetime,
                            "check_out": datetime.datetime(slot.start_datetime.year, slot.start_datetime.month, slot.start_datetime.day, 23, 59),
                            "employee_id": slot.employee_id.id,
                            "rest_hours": slot.rest_time,
                        })
                        attendance.apply_rules()
                        new_day = datetime.datetime(slot.start_datetime.year, slot.start_datetime.month, slot.start_datetime.day, 0, 0) + datetime.timedelta(days=1)
                        while new_day.date() != slot.end_datetime.date():
                            attendance = self.env["hr.attendance"].create({
                                "check_in": new_day,
                                "check_out": datetime.datetime(new_day.year, new_day.month, slot.new_day.day, 23, 59),
                                "employee_id": slot.employee_id.id,
                                "rest_hours": slot.rest_time,
                            })
                            attendance.apply_rules()
                            new_day = new_day + datetime.timedelta(days=1)
                        attendance = self.env["hr.attendance"].create({
                            "check_in": new_day,
                            "check_out": slot.end_datetime.date(),
                            "employee_id": slot.employee_id.id,
                            "rest_hours": slot.rest_time,
                        })
                        attendance.apply_rules()
                        
                    else:
                        attendance = self.env["hr.attendance"].create({
                            "check_in": slot.start_datetime,
                            "check_out": slot.end_datetime,
                            "employee_id": slot.employee_id.id,
                            "rest_hours": slot.rest_time,
                        })
                        attendance.apply_rules()
                    slot.has_synced = True
                except:
                    pass

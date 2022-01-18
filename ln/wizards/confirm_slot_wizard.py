# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError
import datetime
from dateutil.relativedelta import *

class PlanningConfirm(models.TransientModel):
    _name = 'ln.planning.confirm'
    _description = "Send Planning"

    start_datetime = fields.Datetime("Period", required=True, default=lambda self: self.get_default_start_date())
    end_datetime = fields.Datetime("Stop Date", required=True, default=lambda self: self.get_default_end_date())
    note = fields.Text("Extra Message", help="Additional message displayed in the email sent to employees")
    employee_ids = fields.Many2many('hr.employee', string="Resources",
                                    help="Employees who will receive planning by email if you click on publish & send.",
                                    compute='_compute_slots_data', inverse='_inverse_employee_ids', store=True)
    slot_ids = fields.Many2many('planning.slot', compute='_compute_slots_data', store=True)


    def get_default_start_date(self):
        now = datetime.datetime.now()
        return now + datetime.timedelta(7-now.weekday())


    def get_default_end_date(self):
        now = datetime.datetime.now()
        start = now + datetime.timedelta(7-now.weekday())
        return start + relativedelta(month=+4)

    @api.depends('start_datetime', 'end_datetime')
    def _compute_slots_data(self):
        for wiz in self:
            wiz.slot_ids = self.env['planning.slot'].search([('start_datetime', '>=', wiz.start_datetime),
                                                             ('end_datetime', '<=', wiz.end_datetime)])
            wiz.employee_ids = wiz.slot_ids.filtered(lambda s: s.resource_type == 'user').mapped('employee_id')

    def _inverse_employee_ids(self):
        for wiz in self:
            wiz.slot_ids = self.env['planning.slot'].search([('start_datetime', '>=', wiz.start_datetime),
                                                             ('start_datetime', '<=', wiz.end_datetime), ("confirm_status", "=", 'to_confirm')])

    def get_employees_without_work_email(self):
        self.ensure_one()
        if not self.employee_ids.check_access_rights('write', raise_exception=False):
            return None
        employee_ids_without_work_email = self.employee_ids.filtered(lambda employee: not employee.work_email).ids
        if not employee_ids_without_work_email:
            return None
        context = dict(self._context, force_email=True)
        return {
            'relation': 'hr.employee',
            'res_ids': employee_ids_without_work_email,
            'context': context,
        }

    def action_send(self):
        if not self.employee_ids:
            raise UserError(_('Select the employees you would like to send the planning to.'))
        slot_to_send = self.slot_ids.filtered(lambda s: s.employee_id in self.employee_ids)
        if not slot_to_send:
            raise UserError(_('This action is not allowed as there are no shifts planned for the selected time period.'))
        # create the planning
        planning = self.env['ln.planning.planning.confirm'].create({
            'start_datetime': self.start_datetime,
            'end_datetime': self.end_datetime,
            'slot_ids': [(6, 0, slot_to_send.ids)],
        })
        slot_employees = slot_to_send.mapped('employee_id')
        employees_to_send = self.env['hr.employee']
        for employee in self.employee_ids:
            if employee in slot_employees:
                employees_to_send |= employee
        res = planning._send_planning(message=self.note, employees=employees_to_send)
        if res:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("The schedule was successfully sent to your employees."),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
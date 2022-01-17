from odoo import fields, api, models, _
import uuid
import pytz

class PlanningPlanningConfirm(models.Model):
    _name = 'ln.planning.planning.confirm'
    _description = 'Schedule to confirm'

    @api.model
    def _default_access_token(self):
        return str(uuid.uuid4())

    start_datetime = fields.Datetime("Start Date", required=True)
    end_datetime = fields.Datetime("Stop Date", required=True)
    access_token = fields.Char("Security Token", default=_default_access_token, required=True, copy=False, readonly=True)
    slot_ids = fields.Many2many('planning.slot')
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    date_start = fields.Date('Date Start', compute='_compute_dates')
    date_end = fields.Date('Date End', compute='_compute_dates')

    @api.depends('start_datetime', 'end_datetime')
    @api.depends_context('uid')
    def _compute_dates(self):
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        for planning in self:
            planning.date_start = pytz.utc.localize(planning.start_datetime).astimezone(tz).replace(tzinfo=None)
            planning.date_end = pytz.utc.localize(planning.end_datetime).astimezone(tz).replace(tzinfo=None)

    def _compute_display_name(self):
        """ This override is need to have a human readable string in the email light layout header (`message.record_name`) """
        for planning in self:
            planning.display_name = _('Planning à confirmer')

    def _send_planning(self, message=None, employees=False):
        email_from = self.env.user.email or self.env.user.company_id.email or ''
        sent_slots = self.env['planning.slot']
        for planning in self:
            # prepare planning urls, recipient employees, ...
            slots = planning.slot_ids

            # extract planning URLs
            employees = employees or slots.mapped('employee_id')
            employee_url_map = employees.sudo()._planning_confirm_get_url(planning)

            # send planning email template with custom domain per employee
            template = self.env.ref('ln.ln_email_template_planning_planning', raise_if_not_found=False)
            template_context = {
                'slot_total_count': slots and len(slots),
                'message': message,
            }
            if template:
                # /!\ For security reason, we only given the public employee to render mail template
                for employee in self.env['hr.employee.public'].browse(employees.ids):
                    if employee.work_email:
                        template_context['employee'] = employee
                        template_context['start_datetime'] = planning.date_start
                        template_context['end_datetime'] = planning.date_end
                        template_context['planning_url'] = employee_url_map[employee.id]
                        template_context['assigned_new_shift'] = bool(slots.filtered(lambda slot: slot.employee_id.id == employee.id))
                        template.with_context(**template_context).send_mail(planning.id, email_values={'email_to': employee.work_email, 'email_from': email_from}, notif_layout='mail.mail_notification_light')
            sent_slots |= slots
        return True
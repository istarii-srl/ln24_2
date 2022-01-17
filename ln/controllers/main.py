
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licens

from odoo import http, _
from odoo.http import request

import pytz
from odoo.tools.misc import get_lang

from odoo import tools

from .mail_helper import MailHelper


class LNShiftController(http.Controller):

    @http.route(['/confirm/<string:planning_token>/<string:employee_token>'], type='http', auth="public", website=True)
    def planning(self, planning_token, employee_token, message=False, **kwargs):
        """ Displays an employee's calendar and the current list of open shifts """
        planning_data = self._planning_get(planning_token, employee_token, message)
        if not planning_data:
            return request.not_found()
        return request.render('ln.ln_period_report_template', planning_data)

    def _planning_get(self, planning_token, employee_token, message=False):
        employee_sudo = request.env['hr.employee'].sudo().search([('employee_token', '=', employee_token)], limit=1)
        if not employee_sudo:
            return

        planning_sudo = request.env['ln.planning.planning.confirm'].sudo().search([('access_token', '=', planning_token)], limit=1)
        if not planning_sudo:
            return

        employee_tz = pytz.timezone(employee_sudo.tz or 'UTC')
        employee_fullcalendar_data = []
        open_slots = []

        planning_slots = planning_sudo.slot_ids.filtered(lambda s: s.employee_id == employee_sudo)

        # filter and format slots
        slots_start_datetime = []
        slots_end_datetime = []
        # Default values. In case of missing slots (an error message is shown)
        # Avoid errors if the _work_intervals are not defined.
        checkin_min = 8
        checkout_max = 18
        planning_values = {
            'employee_slots_fullcalendar_data': employee_fullcalendar_data,
            'planning_planning_id': planning_sudo,
            'employee': employee_sudo,
            'employee_token': employee_token,
            'planning_token': planning_token,
            'no_data': True
        }
        for slot in planning_slots:
            if planning_sudo.start_datetime <= slot.start_datetime <= planning_sudo.end_datetime:
                # We only display slots starting in the planning_sudo range
                # If a slot is moved outside the planning_sudo range, the url remains valid but the slot is hidden.
                if slot.employee_id:
                    employee_fullcalendar_data.append({
                        'title': '%s%s' % (slot.role_id.name or _("Shift"), u' \U0001F4AC' if slot.name else ''),
                        'start': str(pytz.utc.localize(slot.start_datetime).astimezone(employee_tz).replace(tzinfo=None)),
                        'end': str(pytz.utc.localize(slot.end_datetime).astimezone(employee_tz).replace(tzinfo=None)),
                        'color': self._format_planning_shifts(slot.confirm_status),
                        'alloc_hours': '%d:%02d' % (int(slot.allocated_hours), round(slot.allocated_hours % 1 * 60)),
                        'alloc_perc': slot.allocated_percentage,
                        'slot_id': slot.id,
                        'note': slot.name,
                        'allow_self_unassign': True,
                        'is_unassign_deadline_passed': False,
                        'role': slot.role_id.name,
                        'confirm_status': slot.confirm_status,
                    })
                    # We add the slot start and stop into the list after converting it to the timezone of the employee
                    slots_start_datetime.append(pytz.utc.localize(slot.start_datetime).astimezone(employee_tz).replace(tzinfo=None))
                    slots_end_datetime.append(pytz.utc.localize(slot.end_datetime).astimezone(employee_tz).replace(tzinfo=None))
                elif not slot.is_past and (
                        not employee_sudo.planning_role_ids or not slot.role_id or slot.role_id in employee_sudo.planning_role_ids):
                    open_slots.append(slot)
        # Calculation of the events to define the default calendar view:
        # If the planning_sudo only spans a week, default view is week, else it is month.
        min_start_datetime = planning_sudo.start_datetime
        max_end_datetime = planning_sudo.end_datetime
        if min_start_datetime.isocalendar()[1] == max_end_datetime.isocalendar()[1]:
            # isocalendar returns (year, week number, and weekday)
            default_view = 'timeGridWeek'
        else:
            default_view = 'dayGridMonth'
        # Calculation of the minTime and maxTime values in timeGridDay and timeGridWeek
        # We want to avoid displaying overly large hours range each day or hiding slots outside the
        # normal working hours
        attendances = employee_sudo.resource_calendar_id._work_intervals_batch(
            pytz.utc.localize(planning_sudo.start_datetime),
            pytz.utc.localize(planning_sudo.end_datetime),
            resources=employee_sudo.resource_id, tz=employee_tz
        )[employee_sudo.resource_id.id]
        if attendances and attendances._items:
            checkin_min = min(map(lambda a: a[0].hour, attendances._items))  # hour in the timezone of the employee
            checkout_max = max(map(lambda a: a[1].hour, attendances._items))  # idem
        # We calculate the earliest/latest hour of the slots. It is used in the weekview.
        if slots_start_datetime and slots_end_datetime:
            event_hour_min = min(map(lambda s: s.hour, slots_start_datetime)) # idem
            event_hour_max = max(map(lambda s: s.hour, slots_end_datetime)) # idem
            mintime_weekview, maxtime_weekview = self._get_hours_intervals(checkin_min, checkout_max, event_hour_min,
                                                                           event_hour_max)
        else:
            # Fallback when no slot is available. Still needed because open slots display a calendar
            mintime_weekview, maxtime_weekview = checkin_min, checkout_max
        defaut_start = pytz.utc.localize(planning_sudo.start_datetime).astimezone(employee_tz).replace(tzinfo=None)
        if employee_fullcalendar_data or open_slots:
            planning_values.update({
                'employee_slots_fullcalendar_data': employee_fullcalendar_data,
                'open_slots_ids': open_slots,
                # fullcalendar does not understand complex iso code like fr_BE
                'locale': get_lang(request.env).iso_code.split("_")[0],
                'format_datetime': lambda dt, dt_format: tools.format_datetime(request.env, dt, tz=employee_tz.zone, dt_format=dt_format),
                'notification_text': message in ['assign', 'unassign', 'already_assign', 'deny_unassign'],
                'message_slug': message,
                'has_role': any([s.role_id.id for s in open_slots]),
                'has_note': any([s.name for s in open_slots]),
                # start_datetime and end_datetime are used in the banner. This ensure that these values are
                # coherent with the sended mail.
                'start_datetime': planning_sudo.start_datetime,
                'end_datetime': planning_sudo.end_datetime,
                'mintime': '%02d:00:00' % mintime_weekview,
                'maxtime': '%02d:00:00' % maxtime_weekview,
                'default_view': default_view,
                'default_start': defaut_start.date(),
                'no_data': False
            })
        return planning_values

    @staticmethod
    def _format_planning_shifts(confirm_status):
        """Take a color code from Odoo's Kanban view and returns an hex code compatible with the fullcalendar library"""

        switch_color = {
            'refused': '#EE4B39',   # Red
            'to_confirm': '#F29648',   # Orange
            'confirmed': '#2BAF73',  # Green
        }

        return switch_color[confirm_status]

    @staticmethod
    def _get_hours_intervals(checkin_min, checkout_max, event_hour_min, event_hour_max):
        """
        This method aims to calculate the hours interval displayed in timeGrid
        By default 0:00 to 23:59:59 is displayed.
        We want to display work intervals but if an event occurs outside them, we adapt and display a margin
        to render a nice grid
        """
        if event_hour_min is not None and checkin_min > event_hour_min:
            # event_hour_min may be equal to 0 (12 am)
            mintime = max(event_hour_min - 2, 0)
        else:
            mintime = checkin_min
        if event_hour_max and checkout_max < event_hour_max:
            maxtime = min(event_hour_max + 2, 24)
        else:
            maxtime = checkout_max

        return mintime, maxtime

    
    @http.route('/confirm/<string:token_planning>/<string:token_employee>/assign/<int:slot_id>', type="http", auth="public", website=True)
    def planning_self_assign(self, token_planning, token_employee, slot_id, **kwargs):
        slot_sudo = request.env['planning.slot'].sudo().browse(slot_id)
        if not slot_sudo.exists():
            return request.not_found()

        employee_sudo = request.env['hr.employee'].sudo().search([('employee_token', '=', token_employee)], limit=1)
        if not employee_sudo:
            return request.not_found()

        planning_sudo = request.env['ln.planning.planning.confirm'].sudo().search([('access_token', '=', token_planning)], limit=1)
        if not planning_sudo or slot_sudo.id not in planning_sudo.slot_ids._ids:
            return request.not_found()

        slot_sudo.write({'confirm_status': 'confirmed'})
        return request.redirect('/confirm/%s/%s' % (token_planning, token_employee))

    @http.route('/confirm/<string:token_planning>/<string:token_employee>/unassign/<int:shift_id>', type="http", auth="public", website=True)
    def planning_self_unassign(self, token_planning, token_employee, shift_id, message=False, **kwargs):
        slot_sudo = request.env['planning.slot'].sudo().search([('id', '=', shift_id)], limit=1)
        if not slot_sudo:
            return request.not_found()

        employee_sudo = request.env['hr.employee'].sudo().search([('employee_token', '=', token_employee)], limit=1)
        if not employee_sudo:
            return request.not_found()

        planning_sudo = request.env['ln.planning.planning.confirm'].sudo().search([('access_token', '=', token_planning)], limit=1)
        if not planning_sudo or slot_sudo.id not in planning_sudo.slot_ids._ids:
            return request.not_found()

        slot_sudo.write({'confirm_status': 'refused'})
        #planning_sudo.write({'slot_ids': [(3, slot_sudo.id, 0)]})

        MailHelper.send_refusal_mail(request, employee_id=employee_sudo, slot_id=slot_sudo)        
        return request.redirect('/confirm/%s/%s' % (token_planning, token_employee))

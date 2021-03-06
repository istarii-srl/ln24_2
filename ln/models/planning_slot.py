from odoo import fields, api, models
import datetime

class PlanningSlot(models.Model):
    _name = "planning.slot"
    _inherit = "planning.slot"

    slot_to_confirm = fields.Boolean(string="Slot à confirmer", default=True)
    confirm_status = fields.Selection(string="Statut de confirmation", selection=[("to_confirm", "À confirmer"), ('refused', 'Refusé'), ("confirmed", 'Confirmé')], default="to_confirm", readonly=False)
    has_synced = fields.Boolean(string="Est sync avec présence", default=False)
    has_rest = fields.Boolean(string="Pause dans le shift", compute="_compute_rest")
    rest_time = fields.Float(string="Temps de pause", compute="_compute_rest")
    synchro_attendance = fields.Boolean(string="Synchronisation avec Attendance", default=True)
    refresh_box = fields.Boolean(string="Refresh", default=False)

                 

    @api.depends('template_id')
    def _compute_rest(self):
        for slot in self:
            if slot.template_id:
                slot.has_rest = slot.template_id.has_rest
                slot.rest_time = slot.template_id.rest_time
            else:
                slot.has_rest = False
                slot.rest_time = 0.0

    def change_domain(self):
        for slot in self:
            return slot.on_domain_changed()

    
    @api.onchange('role_id', 'resource_id', 'refresh_box')
    def on_domain_changed(self):
        for slot in self:
            if slot.role_id:
                slots = self.env["planning.slot"].search([("start_datetime", ">", slot.start_datetime - datetime.timedelta(days=2)), ("end_datetime", "<", slot.end_datetime + datetime.timedelta(days=2))])
                employee_ids = slot.role_id.employee_ids.ids
                for slot_near in slots:
                    if (slot_near.start_datetime < slot.start_datetime and slot_near.end_datetime > slot.end_datetime) or (slot_near.start_datetime >= slot.start_datetime and slot_near.start_datetime <= slot.end_datetime) or (slot_near.end_datetime >= slot.start_datetime and slot_near.end_datetime <= slot.end_datetime):
                        if slot_near.resource_id and slot_near.resource_id.employee_single_id.id in employee_ids:
                            employee_ids.remove(slot_near.resource_id.employee_single_id.id)
                if slot.resource_id:
                    return {'domain': {'resource_id': [('employee_single_id', 'in', employee_ids)], 'role_id': [('id', 'in', slot.resource_id.employee_single_id.planning_role_ids.ids)]}}
                else:
                    return  {'domain': {'resource_id': [('employee_single_id', 'in', employee_ids)]}}
            elif slot.resource_id:
                return {'domain': {'role_id': [('id', 'in', slot.resource_id.employee_single_id.planning_role_ids.ids)]}}
            else:
                return {'domain': {'resource_id': [('id', '!=', -1)], 'role_id': [('id', '!=', -1)]}}

    #@api.onchange('')
    #def _on_resource_changed(self):
    #    for slot in self:
    #        if slot.resource_id:
    #            return {'domain': {'role_id': [('id', 'in', slot.resource_id.employee_single_id.planning_role_ids.ids)]}}
    #        else:
    #            return {'domain': {'role_id': [('id', '!=', -1)]}}


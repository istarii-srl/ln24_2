from odoo import fields, api, models

class PlanningSlot(models.Model):
    _name = "planning.slot"
    _inherit = "planning.slot"

    slot_to_confirm = fields.Boolean(string="Slot à confirmer", default=True)
    confirm_status = fields.Selection(string="Statut de confirmation", selection=[("to_assign", "À assigner"), ("to_confirm", "À confirmer"), ('refused', 'Refusé'), ("confirmed", 'Confirmé')], default="to_assign")
    has_synced = fields.Boolean(string="Est sync avec présence", default=False)
    has_rest = fields.Boolean(string="Pause dans le shift", compute="_compute_rest")
    rest_time = fields.Float(string="Temps de pause", compute="_compute_rest")
    synchro_attendance = fields.Boolean(string="Synchronisation avec Attendance", default=True)

    @api.depends('template_id')
    def _compute_rest(self):
        for slot in self:
            if slot.template_id:
                slot.has_rest = slot.template_id.has_rest
                slot.rest_time = slot.template_id.rest_time
            else:
                slot.has_rest = False
                slot.rest_time = 0.0

    @api.onchange('resource_id')
    def on_resource_change(self):
        for slot in self:
            slot.confirm_status = 'to_confirm'

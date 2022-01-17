from odoo import fields, api, models

class PlanningSlot(models.Model):
    _name = "planning.slot"
    _inherit = "planning.slot"

    slot_to_confirm = fields.Boolean(string="Slot à confirmer", default=True)
    confirm_status = fields.Selection(string="Statut de confirmation", selection=[("to_confirm", "À confirmer"), ('refused', 'Refusé'), ("confirmed", 'Confirmé')], default="to_confirm")
    has_synced = fields.Boolean(string="Est sync avec présence", default=False)
    has_rest = fields.Boolean(string="Pause dans le shift", default = False)
    rest_time = fields.Float(string="Temps de pause", default = 0.0)

    @api.onchange('resource_id')
    def on_resource_change(self):
        for slot in self:
            slot.confirm_status = 'to_confirm'

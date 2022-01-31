from odoo import fields, api, models

class SlotTemplate(models.Model):
    _name = "planning.slot.template"
    _inherit = "planning.slot.template"

    has_rest = fields.Boolean(string="Pause dans le shift", default = False)
    rest_time = fields.Float(string="Temps de pause", default = 0.0)
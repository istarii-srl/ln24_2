from odoo import fields, api, models

class PlanningSlot(models.Model):
    _name = "planning.slot"
    _inherit = "planning.slot"

    #role_id = fields.Many2one(domain=lambda self: [('id', 'in', self._get_role_ids())])
    #resource_id = fields.Many2one(domain= lambda self: [('employee_single_id', 'in', self._get_resource_ids())])
    slot_to_confirm = fields.Boolean(string="Slot à confirmer", default=True)
    confirm_status = fields.Selection(string="Statut de confirmation", selection=[("to_confirm", "À confirmer"), ('refused', 'Refusé'), ("confirmed", 'Confirmé')], default="to_confirm", readonly=False)
    has_synced = fields.Boolean(string="Est sync avec présence", default=False)
    has_rest = fields.Boolean(string="Pause dans le shift", compute="_compute_rest")
    rest_time = fields.Float(string="Temps de pause", compute="_compute_rest")
    synchro_attendance = fields.Boolean(string="Synchronisation avec Attendance", default=True)
    fake_compute = fields.Boolean(compute="_compute_domain")

    @api.depends('rest_time')
    def _compute_domain(self):
        for slot in self:
            slot.fake_compute = True
            slot.write({'role_id': slot.role_id.id, 'resource_id':slot.resource_id.id})


    def _get_role_ids(self):
        if self.resource_id:
            return self.resource_id.employee_single_id.planning_role_ids.ids
        else:
            return self.env["planning.role"].search([]).ids
    
    def _get_resource_ids(self):
        if self.role_id:
            return self.role_id.employee_ids.ids
        else:
            return self.env["hr.employee"].search([]).ids

                 

    @api.depends('template_id')
    def _compute_rest(self):
        for slot in self:
            if slot.template_id:
                slot.has_rest = slot.template_id.has_rest
                slot.rest_time = slot.template_id.rest_time
            else:
                slot.has_rest = False
                slot.rest_time = 0.0

    
    @api.onchange('role_id')
    def _on_role_changed(self):
        for slot in self:
            if slot.role_id:
                return {'domain': {'resource_id': [('employee_single_id', 'in', slot.role_id.employee_ids.ids)]}}
            else:
                return {'domain': {'resource_id': [('id', '!=', -1)]}}

    @api.onchange('resource_id')
    def _on_resource_changed(self):
        for slot in self:
            if slot.resource_id:
                return {'domain': {'role_id': [('id', 'in', slot.resource_id.employee_single_id.planning_role_ids.ids)]}}
            else:
                return {'domain': {'role_id': [('id', '!=', -1)]}}


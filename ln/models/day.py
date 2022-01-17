from odoo import fields, models, api

class Day(models.Model):
    _name = "ln.day"
    _description = "Représente un jour de la semaine"

    name = fields.Char(string="Jour de la semaine ")
    day_position = fields.Integer(string="Position du jour dans la semaine", default=1, required=True)
    include_all = fields.Boolean(string="Représente tous les jours de la semaine", default=False)

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleIncentive(models.Model):
    _name = 'sale.incentive'
    _description = "Sale Incentive"
    _rec_name = 'zone'

    zone = fields.Many2one('crm.team', string="Zone")
    target = fields.Float(string="Target")
    amount = fields.Float(string="Amount")
    date_from = fields.Date(string="Date From", required=True)
    date_to = fields.Date(string="Date To", required=True)
    deduction_0_15 = fields.Float(string="0 to 15%", required=True)
    deduction_15_25 = fields.Float(string="15% to 25%", required=True)
    deduction_25_35 = fields.Float(string="25% to 35%", required=True)
    deduction_above_35 = fields.Float(string="Above 35%", required=True)

    @api.onchange('target')
    def _onchange_target(self):
        if self.zone:
            sale_incentive = self.env['crm.team'].search([('id', '=', self.zone.id)])
            for rec in sale_incentive:
                rec.write({'target': self.target})

    @api.onchange('date_to')
    def _onchange_date_to(self):
        if self.date_from and self.date_to:
            if self.date_to < self.date_from:
                raise ValidationError("Date to must be greater than Date from")
            sale_incentive = self.env['crm.team'].search([('id', '=', self.zone.id)])
            for rec in sale_incentive:
                rec.write({'date_to': self.date_to,'date_from': self.date_from})

    @api.onchange('deduction_0_15')
    def _onchange_deduction_0_15(self):
        if self.deduction_0_15:
            sale_incentive = self.env['crm.team'].search([('id', '=', self.zone.id)])
            for rec in sale_incentive:
                rec.write({'deduction_0_15': self.deduction_0_15})

    @api.onchange('deduction_15_25')
    def _onchange_deduction_15_25(self):
        if self.deduction_15_25:
            sale_incentive = self.env['crm.team'].search([('id', '=', self.zone.id)])
            for rec in sale_incentive:
                rec.write({'deduction_15_25': self.deduction_15_25})

    @api.onchange('deduction_25_35')
    def _onchange_deduction_25_35(self):
        if self.deduction_25_35:
            sale_incentive = self.env['crm.team'].search([('id', '=', self.zone.id)])
            for rec in sale_incentive:
                rec.write({'deduction_25_35': self.deduction_25_35})

    @api.onchange('deduction_above_35')
    def _onchange_deduction_above_35(self):
        if self.deduction_above_35:
            sale_incentive = self.env['crm.team'].search([('id', '=', self.zone.id)])
            for rec in sale_incentive:
                rec.write({'deduction_above_35': self.deduction_above_35})

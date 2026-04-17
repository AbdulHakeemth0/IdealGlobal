from odoo import api, fields, models


class CRMTeam(models.Model):
    _inherit = 'crm.team'

    total_sale_amount = fields.Float(string="Total Sale Amount",
                                     compute='_compute_total_sale_amount', store=True)
    target = fields.Char(string="Target", store=True)
    achieved_percentage = fields.Float(string="Achieved Percentage",
                                       compute='_compute_achieved_percentage', store=True)
    deduction_percentage = fields.Float(string="Deduction Percentage", store=True)
    incentive = fields.Float(string='Amount', compute='_compute_incentive', store=True)
    incentive_type = fields.Selection([('deduction', 'Deduction'), ('incentive', 'Incentive')],
                                      string="Type")
    date_to = fields.Date(string="Date To")
    date_from = fields.Date(string="Date From")
    deduction_0_15 = fields.Float(string="0 to 15%")
    deduction_15_25 = fields.Float(string="15% to 25%")
    deduction_25_35 = fields.Float(string="25% to 35%")
    deduction_above_35 = fields.Float(string="Above 35%")

    @api.depends('date_from', 'date_to')
    def _compute_total_sale_amount(self):
        for team in self:
            if team.date_from and team.date_to:
                sales_zone = self.env['sale.order'].search(
                    [('team_id', '=', team.id), ('create_date', '>=', team.date_from),
                     ('create_date', '<=', team.date_to), ('state', '=', 'sale')])
                total_amount = 0
                for rec in sales_zone:
                    print("rec", rec)
                    print("rec.amount_total", rec.amount_total)
                    total_amount += rec.amount_total
                    team.total_sale_amount = total_amount

            # total_amount = sum(team.opportunity_ids.mapped('amount_total'))

    @api.depends('target')
    def _compute_achieved_percentage(self):
        for team in self:
            if team.target and float(team.target) != 0:
                achieved = (float(team.total_sale_amount) / float(team.target)) * 100
                team.achieved_percentage = achieved
                if team.achieved_percentage < 100:
                    team.deduction_percentage = 100 - team.achieved_percentage
            else:
                team.achieved_percentage = 0.0
                # team.deduction_percentage = 100
            if team.deduction_percentage:
                team.incentive_type = 'deduction'
                if team.deduction_percentage > 0 and team.deduction_percentage < 15:
                    team.incentive = -(self.deduction_0_15)
                elif team.deduction_percentage > 15 and team.deduction_percentage < 25:
                    team.incentive = -(self.deduction_15_25)
                elif team.deduction_percentage > 25 and team.deduction_percentage < 35:
                    team.incentive = -(self.deduction_25_35)
                else:
                    team.incentive = -(self.deduction_above_35)
            else:
                team.incentive_type = 'incentive'

    @api.depends('achieved_percentage', 'target')
    def _compute_incentive(self):
        for team in self:
            if team.achieved_percentage >= 100:
                incentive_zone = self.env['sale.incentive'].search([('zone', '=', team.id)])
                for rec in incentive_zone:
                    team.incentive = float(team.target) + float(rec.amount)

    def button_calculate_values(self):
        selected_records = self.env[self._name].browse(self.env.context.get('active_ids'))
        for team in selected_records:
            print("Selected Records", team)
            team._compute_total_sale_amount()
            team._compute_achieved_percentage()
            team._compute_incentive()

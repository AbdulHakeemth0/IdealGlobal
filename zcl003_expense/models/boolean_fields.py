from odoo import fields, models, api, _


class BooleanType(models.Model):

    _inherit = "account.move"



    # container_seq = fields.Char(readonly=True, required=True, copy=False, default=lambda self: _('New'))
    # purchase_seq = fields.Char(readonly=True, required=True, copy=False, default=lambda self: _('New'))
    container_exp = fields.Boolean(string='Container Expense', default=False)
    purchase_exp = fields.Boolean(string='Purchase Expense', default=False)
    salary_exp = fields.Boolean(string='Salary Expense', default=False)
    # salary_seq = fields.Char(readonly=True, required=True, copy=False, default=lambda self: _('New'))
    branch_exp = fields.Boolean(string='Branch Expense', default=False)
    # branch_seq = fields.Char(readonly=True, required=True, copy=False, default=lambda self: _('New'))
    transfer_exp = fields.Boolean(string='Transfer Expense', default=False)
    # transfer_seq = fields.Char(readonly=True, required=True, copy=False, default=lambda self: _('New'))
    general_exp = fields.Boolean(string='General Expense', default=False)
    # general_seq = fields.Char(readonly=True, required=True, copy=False, default=lambda self: _('New'))
    closingentries_exp = fields.Boolean(string='Closing Enteries Expense', default=False)
    # closingentries_seq = fields.Char(readonly=True, required=True, copy=False, default=lambda self: _('New'))
    normal_exp = fields.Boolean(string='Normal Expense', default=False)
    container_no = fields.Integer(string='Container No')
    internal_code = fields.Char(string='Internal Code')
    bill_no = fields.Char(string='Bill No')

    # @api.model
    # def create(self, vals):
    #     if vals.get('container_seq', _('New')) == _('New'):
    #         vals['container_seq'] = self.env['ir.sequence'].next_by_code('container.sequence') or _('New')
    #     if vals.get('purchase_seq', _('New')) == _('New'):
    #         vals['purchase_seq'] = self.env['ir.sequence'].next_by_code('purchase.sequence') or _('New')
    #     if vals.get('salary_seq', _('New')) == _('New'):
    #         vals['salary_seq'] = self.env['ir.sequence'].next_by_code('salary.sequence') or _('New')
    #     if vals.get('branch_seq', _('New')) == _('New'):
    #         vals['branch_seq'] = self.env['ir.sequence'].next_by_code('branch.sequence') or _('New')
    #     if vals.get('transfer_seq', _('New')) == _('New'):
    #         vals['transfer_seq'] = self.env['ir.sequence'].next_by_code('transfer.sequence') or _('New')
    #     if vals.get('general_seq', _('New')) == _('New'):
    #         vals['general_seq'] = self.env['ir.sequence'].next_by_code('general.sequence') or _('New')
    #     if vals.get('closingentries_seq', _('New')) == _('New'):
    #         vals['closingentries_seq'] = self.env['ir.sequence'].next_by_code('closeentry.sequence') or _('New')
    #     res = super(BooleanType, self).create(vals)
    #     return res

    # def name_get(self):
    #     result = []
    #     for move in self:
    #         if move.container_exp == True:
    #             result.append((move.id, move.container_seq))
    #         elif move.purchase_exp == True:
    #             result.append((move.id, move.purchase_seq))
    #         elif move.salary_exp == True:
    #             result.append((move.id, move.salary_seq))
    #         elif move.branch_exp == True:
    #             result.append((move.id, move.branch_seq))
    #         elif move.transfer_exp == True:
    #             result.append((move.id, move.transfer_seq))
    #         elif move.general_exp == True:
    #             result.append((move.id, move.general_seq))
    #         elif move.closingentries_exp == True:
    #             result.append((move.id, move.closingentries_seq))
    #
    #         else:
    #             result.append((move.id, move.name))
    #     return result

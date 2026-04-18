from odoo import api, fields, models


class BvMultiPricelistWizard(models.TransientModel):
    _name = 'bv.multi.pricelist.wizard'
    _description = 'Multi Pricelist Wizard'

    bv_order_line_id = fields.Many2one('sale.order.line', string='Order Line')
    bv_pricelist_line_ids = fields.One2many(
        'bv.multi.pricelist.wizard.line',
        'wizard_id',
        string='Pricelist Lines'
    )

    def action_remove_pricelist(self):
        self.ensure_one()
        order_line = self.bv_order_line_id
        if order_line:
            order_line.write({'bv_line_pricelist_id': False})
            order_line.with_context(force_price_recomputation=True)._compute_price_unit()
        return {'type': 'ir.actions.act_window_close'}


class BvMultiPricelistWizardLine(models.TransientModel):
    _name = 'bv.multi.pricelist.wizard.line'
    _description = 'Multi Pricelist Wizard Line'

    wizard_id = fields.Many2one('bv.multi.pricelist.wizard', string='Wizard', ondelete='cascade')
    bv_pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    bv_unit_price = fields.Float(string='Unit Price')
    bv_unit_cost = fields.Float(string='Unit Cost')
    bv_margin = fields.Float(string='Margin')
    bv_margin_percentage = fields.Float(string='Margin (%)')

    def action_apply_pricelist(self):
        self.ensure_one()
        order_line = self.wizard_id.bv_order_line_id
        if not order_line:
            return {'type': 'ir.actions.act_window_close'}
        if not self.bv_pricelist_id:
            return {'type': 'ir.actions.act_window_close'}

        order_line.write({
            'bv_line_pricelist_id': self.bv_pricelist_id.id,
            'price_unit': self.bv_unit_price,
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_open_pricelist(self):
        self.ensure_one()
        if not self.bv_pricelist_id:
            return
        return {
            'name': 'Pricelist',
            'type': 'ir.actions.act_window',
            'res_model': 'product.pricelist',
            'res_id': self.bv_pricelist_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

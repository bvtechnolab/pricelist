from odoo import api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bv_line_pricelist_id = fields.Many2one('product.pricelist', string='Line Pricelist')
    bv_cost_price = fields.Float(string='Cost Price', compute='_compute_bv_cost_price', store=True)
    bv_margin_amount = fields.Float(string='Margin Amount', compute='_compute_bv_margin_amount', store=True)
    bv_margin_percentage = fields.Float(string='Margin (%)', compute='_compute_bv_margin_percentage', store=True)
    bv_multi_pricelist_enabled = fields.Boolean(
        string='Multi Pricelist Enabled',
        compute='_compute_bv_multi_pricelist_enabled',
    )

    def _compute_bv_multi_pricelist_enabled(self):
        enabled = self.env['ir.config_parameter'].sudo().get_param(
            'bv_multi_pricelist.enable_multi_pricelist'
        ) == 'True'
        for line in self:
            line.bv_multi_pricelist_enabled = enabled

    @api.depends('product_id', 'product_id.standard_price')
    def _compute_bv_cost_price(self):
        for line in self:
            if line.product_id:
                line.bv_cost_price = line.product_id.standard_price
            else:
                line.bv_cost_price = 0.0

    @api.depends('price_unit', 'bv_cost_price')
    def _compute_bv_margin_amount(self):
        for line in self:
            line.bv_margin_amount = (line.price_unit or 0.0) - (line.bv_cost_price or 0.0)

    @api.depends('bv_margin_amount', 'bv_cost_price')
    def _compute_bv_margin_percentage(self):
        for line in self:
            if line.bv_cost_price and line.bv_cost_price != 0.0:
                line.bv_margin_percentage = (line.bv_margin_amount / line.bv_cost_price) * 100.0
            else:
                line.bv_margin_percentage = 0.0

    @api.onchange('product_id', 'product_uom_qty', 'bv_line_pricelist_id')
    def _onchange_bv_pricelist(self):
        enabled = self.env['ir.config_parameter'].sudo().get_param(
            'bv_multi_pricelist.enable_multi_pricelist'
        ) == 'True'
        if not enabled:
            return
        for line in self:
            if not line.product_id:
                continue
            # Only trigger when bv_line_pricelist_id is explicitly set
            if not line.bv_line_pricelist_id:
                continue
            pricelist = line.bv_line_pricelist_id
            qty = line.product_uom_qty or 1.0
            try:
                price = pricelist._get_product_price(
                    product=line.product_id,
                    quantity=qty,
                    currency=line.order_id.currency_id,
                    date=line.order_id.date_order,
                    uom=line.product_uom_id,
                )
                line.price_unit = price
            except Exception:
                # Fallback: if pricelist computation fails, keep current price
                pass

    def action_open_bv_pricelist_wizard(self):
        self.ensure_one()
        enabled = self.env['ir.config_parameter'].sudo().get_param(
            'bv_multi_pricelist.enable_multi_pricelist'
        ) == 'True'
        if not enabled:
            return {'type': 'ir.actions.act_window_close'}

        # Guard: no product selected
        if not self.product_id:
            raise UserError("Please select a product before applying a pricelist.")

        wizard = self.env['bv.multi.pricelist.wizard'].create({
            'bv_order_line_id': self.id,
        })
        pricelists = self.env['product.pricelist'].search([])
        if not pricelists:
            raise UserError("No pricelists found. Please create at least one pricelist.")

        wizard_lines = []
        for pricelist in pricelists:
            qty = self.product_uom_qty or 1.0
            try:
                price = pricelist._get_product_price(
                    product=self.product_id,
                    quantity=qty,
                    currency=self.order_id.currency_id,
                    date=self.order_id.date_order,
                    uom=self.product_uom_id,
                )
            except Exception:
                price = 0.0

            cost = self.product_id.standard_price or 0.0
            margin = price - cost
            margin_pct = (margin / cost * 100.0) if cost and cost != 0.0 else 0.0

            wizard_lines.append((0, 0, {
                'bv_pricelist_id': pricelist.id,
                'bv_unit_price': price,
                'bv_unit_cost': cost,
                'bv_margin': margin,
                'bv_margin_percentage': margin_pct,
            }))

        wizard.bv_pricelist_line_ids = wizard_lines

        return {
            'name': 'Apply Pricelist',
            'type': 'ir.actions.act_window',
            'res_model': 'bv.multi.pricelist.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

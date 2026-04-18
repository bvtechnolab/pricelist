from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    bv_multi_pricelist_enabled = fields.Boolean(
        string='Multi Pricelist Enabled',
        compute='_compute_bv_multi_pricelist_enabled',
    )

    def _compute_bv_multi_pricelist_enabled(self):
        enabled = self.env['ir.config_parameter'].sudo().get_param(
            'bv_multi_pricelist.enable_multi_pricelist'
        ) == 'True'
        for order in self:
            order.bv_multi_pricelist_enabled = enabled

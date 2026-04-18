from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    bv_enable_multi_pricelist = fields.Boolean(
        string="Multi Pricelist per Line",
        config_parameter='bv_multi_pricelist.enable_multi_pricelist',
        help="Allow applying different pricelists per sale order line.",
    )

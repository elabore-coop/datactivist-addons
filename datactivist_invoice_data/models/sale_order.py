# -*- coding: utf-8 -*-

from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("partner_id")
    def _compute_fields(self):
        for record in self:
            record.siret = record.partner_id.siret
            record.fr_chorus_service_id = record.partner_id.fr_chorus_service_id

    siret = fields.Char(
        compute="_compute_fields",
        store=True,
        readonly=False,
        help="The SIRET number is the official identity number of this "
        "company's office in France. It is composed of the 9 digits "
        "of the SIREN number and the 5 digits of the NIC number, ie. "
        "14 digits.",
    )

    fr_chorus_service_id = fields.Many2one(
        "chorus.partner.service",
        compute="_compute_fields",
        string="Chorus Service",
        ondelete="restrict",
        tracking=True,
    )

    legal_commitment = fields.Char(string="Legal commitment", store=True)

    market_number = fields.Char(string="Market Number", store=True)

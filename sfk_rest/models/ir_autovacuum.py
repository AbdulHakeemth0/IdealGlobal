import logging

from odoo import models, api

_logger = logging.getLogger(__name__)


class AutoVacuum(models.AbstractModel):
    _inherit = 'ir.autovacuum'

    @api.model
    def power_on(self, *args, **kwargs):
        self.env['sfk_rest.token']._garbage_collect()
        return super(AutoVacuum, self).power_on(*args, **kwargs)

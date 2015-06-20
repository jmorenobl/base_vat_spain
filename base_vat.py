# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv
from openerp.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)


class res_partner(osv.osv):
    _inherit = 'res.partner'

    def _isEU(self, vat):
        if not vat[0:2].encode('utf-8').isalpha():
            return False

    def check_vat(self, cr, uid, ids, context=None):
        user_company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        if user_company.vat_check_vies:
            # force full VIES online check
            check_func = self.vies_vat_check
        else:
            # quick and partial off-line checksum validation
            check_func = self.simple_vat_check
        for partner in self.browse(cr, uid, ids, context=context):
            if not partner.vat:
                continue

            if self._isEU(partner.vat):
                vat_country, vat_number = self._split_vat(partner.vat)
            else:
                vat_country = 'es'  # HACK: this should be get from company info. Can anyone help?
                vat_number = partner.vat

            if not check_func(cr, uid, vat_country, vat_number, context=context):
                _logger.info(_("Importing VAT Number [%s] is not valid !" % vat_number))
                return False
        return True

    def _construct_constraint_msg(self, cr, uid, ids, context=None):
        def default_vat_check(cn, vn):
            # by default, a VAT number is valid if:
            #  it starts with 2 letters
            #  has more than 3 characters
            return cn[0] in string.ascii_lowercase and cn[1] in string.ascii_lowercase
        vat_country, vat_number = self._split_vat(self.browse(cr, uid, ids)[0].vat)
        vat_no = "'CC##' (CC=Country Code, ##=VAT Number)"
        error_partner = self.browse(cr, uid, ids, context=context)
        if default_vat_check(vat_country, vat_number):
            vat_no = _ref_vat[vat_country] if vat_country in _ref_vat else vat_no
            if self.pool['res.users'].browse(cr, uid, uid).company_id.vat_check_vies:
                return '\n' + _('The VAT number [%s] for partner [%s] either failed the VIES VAT validation check or did not respect the expected format %s.') % (error_partner[0].vat, error_partner[0].name, vat_no)
        return '\n' + _('The VAT number [%s] for partner [%s] does not seem to be valid. \nNote: the expected format is %s') % (error_partner[0].vat, error_partner[0].name, vat_no)

    _constraints = [(check_vat, _construct_constraint_msg, ["vat"])]

    def check_vat_es(self, vat):
        return True

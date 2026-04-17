# -*- coding: utf-8 -*-
###################################################################################

# Author       :  Athira M
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

# This program is free software:
# you can modify it under the terms of the GNU Lesser General Public License (LGPL) as
# published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

###################################################################################

{
  "name": "Sale Free Of Cost",
  "summary": """Free Of Cost module for Sale""",
  "category": "Sales",
  "version": "16.0.1.0.0",
  "sequence": 101,
  "author": "Zinfog Codelabs Pvt Ltd",
  "license": "LGPL-3",
  "website": "https://www.zinfog.com",
  "description": """ This module is defined for allowing special discount for Each FOC types""",
  "depends": ['base', 'contacts', 'mail', 'sale_management', 'sale'],
  "data": [
    'security/ir.model.access.csv',
    'views/sale_foc.xml',
    'views/sale_form_view.xml',
    'views/category_foc.xml',
    'data/sequence.xml',
    'wizards/foc_wizard.xml',
    'wizards/categ_foc_wizard.xml'
  ],
  "application": True,
  "installable": True,
  "auto_install": False,
}

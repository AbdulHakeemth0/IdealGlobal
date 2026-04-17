# -*- coding: utf-8 -*-
###################################################################################

# Author       :  Abin suresh
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

# This program is free software:
# you can modify it under the terms of the GNU Lesser General Public License (LGPL) as
# published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

###################################################################################

{
  "name"                    :   "Post Date Cheque",
  "summary"              :   """Post date cheque module for creating post date cheques from accounting module""",
  "category"               :   "Sales",
  "version"                 :   "16.0.1.0.0",
  "sequence"             :   100,
  "author"                  :    "Zinfog Codelabs Pvt Ltd",
  "license"                 :    "LGPL-3",
  "website"                :    "https://www.zinfog.com",
  "description"           :    """ This module is defined for creating post date cheques under accounting """,
  "depends"               :   ['base','account','mail'],
  "data"                      :   ['security/ir.model.access.csv',
                                      'views/account_pdc_view.xml',
                                   ],
  "application"                      :    True,
  "installable"                       :    True,
  "auto_install"                     :    False,
}

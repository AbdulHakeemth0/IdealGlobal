import os
import re
import json
import inspect
import logging
import tempfile
import datetime
from datetime import datetime, timedelta
import traceback
import requests
from docutils.nodes import date
from werkzeug import exceptions
import odoo
from odoo import _, fields
from odoo import api
from odoo import http
from odoo import models
from odoo import release
from odoo.http import request
from odoo.http import Response
from odoo.tools.misc import str2bool
import random
import string
from operator import itemgetter
import collections
import pprint
import base64

_logger = logging.getLogger(__name__)

REST_VERSION = {
    'server_version': release.version,
    'server_version_info': release.version_info,
    'server_serie': release.serie,
    'api_version': 2,
}

NOT_FOUND = {
    'error': 'unknown_command',
}

DB_INVALID = {
    'error': 'invalid_db',
}

FORBIDDEN = {
    'error': 'token_invalid',
}

NO_API = {
    'error': 'rest_api_not_supported',
}

LOGIN_INVALID = {
    'error': 'invalid_login',
}

DBNAME_PATTERN = '^[a-zA-Z0-9][a-zA-Z0-9_.-]+$'

Auth_key = 'key=AAAAqml-PGE:APA91bEPKqBbGHannr2U6TNNlpcLtdhowFdfU0F8fuUlieyPodQwGKCn8YFTqBTvPzJAVqXI' \
           '-7V1ARflugl4V_kpGQFXsV8-Rxyf1UjmEDqc1bI1oWt6wDoNQMAC_DegrL74DiOVRlFG '


def abort(message, rollback=False, status=403):
    response = Response(json.dumps(message,
                                   sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=status)
    if request._cr and rollback:
        request._cr.rollback()
    exceptions.abort(response)


def check_token():
    token = request.params.get('token') and request.params.get('token').strip()
    print(token)
    if not token:
        abort(FORBIDDEN)
    env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
    uid = env['sfk_rest.token'].check_token(token)
    if not uid:
        abort(FORBIDDEN)
    request._uid = uid
    request._env = api.Environment(request.cr, uid,
                                   request.session.context or {})


def ensure_db():
    db = request.params.get('db') and request.params.get('db').strip()
    if db and db not in http.db_filter([db]):
        db = None
    if not db and request.session.db and http.db_filter([request.session.db]):
        db = request.session.db
    if not db:
        db = http.db_monodb(request.httprequest)
    if not db:
        abort(DB_INVALID, status=404)
    if db != request.session.db:
        request.session.logout()
    request.session.db = db
    try:
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        module = env['ir.module.module'].search([['name', '=', "sfk_rest"]],
                                                limit=1)
        if module.state != 'installed':
            abort(NO_API, status=500)
    except Exception as error:
        _logger.error(error)
        abort(DB_INVALID, status=404)


def check_params(params):
    missing = []
    for key, value in params.items():
        if not value:
            missing.append(key)
    if missing:
        abort({'error': "arguments_missing %s" % str(missing)}, status=400)


class ObjectEncoder(json.JSONEncoder):
    def default(self, obj, item=None):
        def encode(item):
            if isinstance(item, models.BaseModel):
                vals = {}
                for name, field in item._fields.items():
                    if name in item:
                        if isinstance(item[name], models.BaseModel):
                            records = item[name]
                            if len(records) == 1:
                                vals[name] = (
                                    records.id, records.sudo().display_name)
                            else:
                                val = []
                                for record in records:
                                    val.append(
                                        (record.id, record.sudo().display_name))
                                vals[name] = val
                        else:
                            try:
                                vals[name] = item[name].decode()
                            except UnicodeDecodeError:
                                vals[name] = item[name].decode('latin-1')
                            except AttributeError:
                                vals[name] = item[name]
                    else:
                        vals[name] = None
                return vals
            if inspect.isclass(item):
                return item.__dict__
            try:
                return json.JSONEncoder.default(self, item)
            except TypeError:
                return "error"

        try:
            try:
                result = {}
                for key, value in obj.items():
                    result[key] = encode(item)
                return result
            except AttributeError:
                result = []
                for item in obj:
                    result.append(encode(item))
                return result
        except TypeError:
            return encode(item)


class RESTController(http.Controller):

    # ----------------------------------------------------------
    # General
    # ----------------------------------------------------------

    # LOGIN API

    @http.route('/api/authenticate', auth="none", type='json', methods=['POST'],
                csrf=False)
    def api_authenticate(self, db=None, login=None, password=None, **kw):
        ensure_db()
        data = json.loads(request.httprequest.data)
        print(data)
        response = {

        }
        try:
            uid = request.session.authenticate(data['db'], data['login'],
                                               data['password'])
        except Exception as error:
            response.update({
                'status': 401,
                'msg': "Username or Password Incorrect"
            })
            return response
        if uid:
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            user = request.env['res.users'].sudo().search([('id', '=', uid)])
            token = env['sfk_rest.token'].generate_token(uid)
            response.update({
                'token': token.token,
                'uid': uid,
                'status': 200,
                'name': user.name,
                'msg': "Success"
            })
            return response
        else:
            response.update({
                'status': 401,
                'msg': "Username or Password Incorrect"
            })
            return response

    ################################ USER PROFILE ####################################

    @http.route([
        '/api/search/user/profile'], auth="public", type='http', csrf=False)
    def search_user_profile(self, token=None, **kw):
        user_profile_list = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        user_id = kw.get('user_id')
        name = kw.get('name')
        try:
            if uid:
                if user_id:
                    user_details = request.env['res.users'].sudo().search(
                        [('id', '=', int(user_id)), ('name', 'ilike', name)])
                    current_date = datetime.now().date()
                    start_date = current_date.replace(day=1)
                    sale_orders = request.env['sale.order'].sudo().search([
                        ('user_id', '=', int(user_id)),
                        ('date_order', '>=', start_date),
                        ('date_order', '<=', current_date),
                        ('state', 'in', ('sale', 'done'))

                    ])
                    sub_total = sum(order.amount_total for order in sale_orders)
                    if user_details:
                        for i in user_details:
                            # image_binary_data = i.image_1920
                            # base64_encoded_image = base64.b64encode(image_binary_data).decode('utf-8')
                            dic = {
                                'id': i.id if i.id else None,
                                'name': i.name if i.name else None,
                                'mobile': i.mobile if i.mobile else None,
                                'email': i.login if i.login else None,
                                'sale_revenue': "{:.3f}".format(sub_total),
                                # 'image':base64_encoded_image
                            }
                            user_profile_list.append(dic)
                    msg = "Success"
                    success = True
                    if user_profile_list:
                        return Response(json.dumps(
                            {"data": user_profile_list, 'message': msg,
                             'success': success},
                            sort_keys=True, indent=4, cls=ObjectEncoder),
                            content_type='application/json;charset=utf-8',
                            status=200)
                    else:
                        msg = "Failed"
                        success = False
                        result = None
                        return Response(json.dumps(
                            {"data": result, 'message': msg,
                             'success': success},
                            sort_keys=True, indent=4, cls=ObjectEncoder),
                            content_type='application/json;charset=utf-8',
                            status=202)

            msg = "Token authentication failed"
            success = False
            result = None
            return Response(
                json.dumps({"data": result, 'message': msg, 'success': success},
                           sort_keys=True, indent=4, cls=ObjectEncoder),
                content_type='application/json;charset=utf-8', status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ############################SEARCH CUSTOMER###########################################################
    @http.route([
        '/api/search/customer/profile'], auth="public", type='http', csrf=False)
    def search_customer_profile(self, token=None, **kw):
        customer_list = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        user_id = kw.get('user_id')
        over_due = 0
        amount_due = 0
        try:
            if uid:
                customer = request.env['res.partner'].sudo().search(
                    [('user_id', '=', int(user_id))])
                if customer:
                    for j in customer:
                        current_date = datetime.now().date()
                        start_date = current_date.replace(day=1)
                        # sale_orders = request.env['sale.order'].sudo().search([
                        #     ('partner_id', '=', int(i.id)),
                        #     ('user_id', '=', int(user_id)),
                        #     ('date_order', '>=', start_date),
                        #     ('date_order', '<=', current_date),
                        #     ('state', 'in', ('sale','done'))
                        # ])
                        # print(i.name,sale_orders, 'sale oredersssssssssssss')
                        # sub_total = sum(order.amount_total for order in sale_orders)
                        # # if not sub_total:
                        # #     break
                        # print(sub_total, 'qqqqqqqqqqqqqqqqqqqqqqqq')
                        #
                        #
                        #
                        #
                        #
                        # journals_debit = request.env['account.move.line'].search(
                        #     [('partner_id.id', '=', i.id),
                        #      ('account_id.id', '=', i.property_account_receivable_id.id),
                        #      ('parent_state', '=', 'posted')])
                        # journals_credit = request.env['account.move.line'].search(
                        #     [('partner_id.id', '=', i.id),
                        #      ('parent_state', '=', 'posted')])
                        # if not journals_debit:
                        #     balance_debit = 0
                        # else:
                        #     for journal in journals_debit:
                        #         balance_debit = balance_debit + journal.debit
                        #
                        #     print(balance_debit,i.name, 'balanceee debittttt')
                        #
                        # if not journals_credit:
                        #     balance_credit = 0
                        # else:
                        #
                        #
                        #     for journal in journals_credit:
                        #         balance_credit = balance_credit + journal.credit
                        #     print(balance_credit,i.name,'balanceeeeeeeeee')
                        #
                        # balance = round(balance_credit - balance_debit, 2)
                        # print()
                        partner = request.env['account.move'].sudo().search(
                            [('user_id', '=', int(user_id)),
                             ('payment_state', '!=', 'paid'),
                             ('move_type', '=', 'out_invoice'),
                             ('invoice_date', '>=', start_date),
                             ('invoice_date', '<=', current_date),
                             ('partner_id', '=', j.id)
                             ])
                        if partner:
                            over_due = 0
                            amount_due = 0
                            amount_totals = 0
                            for i in partner:
                                amount_totals += i.amount_total
                                due_day = i.due_days
                                invoice_date = i.invoice_date
                                due_date = invoice_date + timedelta(
                                    days=int(due_day))

                                due_date_datetime = datetime.combine(due_date,
                                                                     datetime.min.time())
                                if due_date_datetime <= datetime.now():
                                    amount_due += i.amount_residual
                                else:
                                    over_due += i.amount_residual

                            dic = {
                                'id': j.id if j.id else None,
                                'name': j.name if j.name else None,
                                'street': j.street if j.street else None,
                                'city': j.city if j.city else None,
                                'state': j.state_id.name if j.state_id else None,
                                'postal_code': j.zip if j.zip else None,
                                'phone': j.phone if j.phone else None,
                                'mobile': j.mobile if j.mobile else None,
                                'amount_due': "{:.3f}".format(amount_due),
                                'price_list': j.property_product_pricelist.pricelist_category_id.id if j.property_product_pricelist.pricelist_category_id else None,
                                'over_due': "{:.3f}".format(over_due),
                                'email': j.email if j.email else None,
                                'total': amount_due + over_due
                            }
                            customer_list.append(dic)
                        else:
                            dic = {
                                'id': j.id if j.id else None,
                                'name': j.name if j.name else None,
                                'street': j.street if j.street else None,
                                'city': j.city if j.city else None,
                                'state': j.state_id.name if j.state_id else None,
                                'postal_code': j.zip if j.zip else None,
                                'phone': j.phone if j.phone else None,
                                'mobile': j.mobile if j.mobile else None,
                                'price_list': j.property_product_pricelist.pricelist_category_id.id if j.property_product_pricelist.pricelist_category_id else None,
                                'amount_due': "{:.3f}".format(0),
                                'over_due': "{:.3f}".format(0),
                                'email': j.email if j.email else None,
                                'total': 0
                            }
                            customer_list.append(dic)

                    msg = "Success"
                    success = True
                    return Response(json.dumps(
                        {"data": customer_list, 'message': msg,
                         'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "Failed"
                    success = False
                    result = None
                    return Response(json.dumps(
                        {"data": result, 'message': msg, 'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)

            msg = "Token authentication failed"
            success = False
            result = None
            return Response(
                json.dumps({"data": result, 'message': msg, 'success': success},
                           sort_keys=True, indent=4, cls=ObjectEncoder),
                content_type='application/json;charset=utf-8', status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ########Search state #################

    @http.route([
        '/api/search/state'], auth="public", type='http', csrf=False)
    def search_state(self, token=None, **kw):
        state_list = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)

        try:
            if uid:
                state_details = request.env['res.country.state'].sudo().search(
                    [])

                if state_details:
                    for i in state_details:
                        dic = {
                            'id': i.id if i.id else None,
                            'name': i.name if i.name else None
                        }
                        state_list.append(dic)
                    msg = "Success"
                    success = True
                    return Response(json.dumps(
                        {"data": state_list, 'message': msg,
                         'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "Failed"
                    success = False
                    result = None
                    return Response(json.dumps(
                        {"data": result, 'message': msg, 'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)

            msg = "Token authentication failed"
            success = False
            result = None
            return Response(
                json.dumps({"data": result, 'message': msg, 'success': success},
                           sort_keys=True, indent=4, cls=ObjectEncoder),
                content_type='application/json;charset=utf-8', status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ###############Create New Customer Post Method without list#######################
    # changes

    @http.route(['/api/create/new/customer/<string:token>/'], auth="public",
                methods=['POST'], type='json', csrf=False)
    def create_new_customer(self, token, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            if uid:
                country = request.env['res.country'].sudo().search(
                    [('code', '=', 'OM'), ('name', '=', 'Oman')])
                partner = request.env['res.partner'].sudo().create({
                    'name': data.get('name'),
                    'building_name': data.get('building'),
                    'street': data.get('streets'),
                    'city': data.get('city'),
                    'state_id': int(data.get('state_id')),
                    'country_id': country.id,
                    'zip': data.get('zip'),
                    # 'phone': int(data.get('phone')),
                    'mobile': int(data.get('mobile')),
                    'email': data.get('email'),
                    'user_id': int(data.get('user_id')),
                    'company_type': 'person',
                })
                return {'status': 200,
                        'message': 'Customer Created successfully.',
                        'partner_id': partner.id}
            else:
                return {'status': 202, 'message': 'Token Expired'}
        except KeyError as key_error:
            return {'status': 202,
                    'message': f"Missing required parameter: {str(key_error)}"}
        except Exception as error:
            _logger.error(error)
            return {'status': 400,
                    'message': 'An error occurred during Customer creation.'}

    #########################product list based on category###########################################################

    @http.route([
        '/api/search/product/list'], auth="public", type='http', csrf=False)
    def search_product_list(self, token=None, **kw):
        product_list_category = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        name = kw.get('name')
        category_id = request.env['product.category'].sudo().search(
            [('id', '=', int(kw.get('category_id')))])
        partner_id = request.env['res.partner'].sudo().search(
            [('id', '=', int(kw.get('partner_id')))])
        try:
            price_list_product = []
            if uid:
                if category_id:
                    if partner_id:
                        if name:
                            product_list = request.env[
                                'product.product'].sudo().search(
                                [('name', 'ilike', name),
                                 ('categ_id', '=', int(category_id))]).ids
                        else:
                            product_list = request.env[
                                'product.product'].sudo().search(
                                [('categ_id', '=', int(category_id))]).ids
                        if partner_id.property_product_pricelist:
                            for rec in partner_id.property_product_pricelist.item_ids:
                                if rec.product_tmpl_id.categ_id.id == category_id.id:
                                    price_list_product.append(
                                        rec.product_tmpl_id.id)
                                    dic = {
                                        'id': rec.product_tmpl_id.id if rec.product_tmpl_id.id else None,
                                        'name': rec.product_tmpl_id.name if rec.product_tmpl_id.name else None,
                                        'product_type': rec.product_tmpl_id.detailed_type if rec.product_tmpl_id.detailed_type else None,
                                        'product_category': rec.product_tmpl_id.categ_id.id if rec.product_tmpl_id.categ_id else None,
                                        'product_image': rec.product_tmpl_id.image_url,
                                        'arabic_name': rec.product_tmpl_id.name_arabic,
                                        'product_code': rec.product_tmpl_id.product_code,
                                        'product_amount': "{:.3f}".format(
                                            rec.product_tmpl_id.product_amount),
                                        'product_discount': rec.product_tmpl_id.product_discount,
                                        'product_price': "{:.3f}".format(rec.fixed_price),
                                        'box': rec.product_tmpl_id.box,
                                        'bag': rec.product_tmpl_id.bag,
                                        'description': rec.product_tmpl_id.description_sale,
                                        'onhand_qty': rec.product_tmpl_id.qty_available
                                    }
                                    product_list_category.append(dic)
                        product_sorted_list = request.env[
                            'product.product'].sudo().browse(
                            [item for item in product_list if
                             item not in price_list_product]).exists()
                        if product_sorted_list:
                            for i in product_sorted_list:
                                dic = {
                                    'p_id': i.product_tmpl_id.id if i.product_tmpl_id else None,
                                    'id': i.id if i.id else None,
                                    'name': i.name if i.name else None,
                                    'product_type': i.detailed_type if i.detailed_type else None,
                                    'product_category': i.categ_id.id if i.categ_id else None,
                                    'product_image': i.product_tmpl_id.image_url,
                                    'product_code': i.product_tmpl_id.product_code,
                                    'product_amount': "{:.3f}".format(
                                        i.product_tmpl_id.product_amount),
                                    'product_discount': i.product_tmpl_id.product_discount,
                                    'product_price': "{:.3f}".format(i.product_tmpl_id.list_price),
                                    'box': i.product_tmpl_id.box,
                                    'bag': i.product_tmpl_id.bag,
                                    'description': i.product_tmpl_id.description_sale,
                                    'onhand_qty': i.qty_available
                                }
                                product_list_category.append(dic)
                        return Response(json.dumps(
                            {"data": product_list_category,
                             'message': 'Success', 'success': True},
                            sort_keys=True, indent=4, cls=ObjectEncoder),
                            content_type='application/json;charset=utf-8',
                            status=200)
                    else:
                        return Response(json.dumps(
                            {"data": None, 'message': 'Partner not found',
                             'success': False}, sort_keys=True, indent=4,
                            cls=ObjectEncoder),
                            content_type='application/json;charset=utf-8',
                            status=202)
                else:
                    return Response(json.dumps(
                        {"data": None, 'message': 'Category not found',
                         'success': False}, sort_keys=True, indent=4,
                        cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)
            else:
                return Response(json.dumps(
                    {"data": None, 'message': 'Token authentication failed',
                     'success': False}, sort_keys=True, indent=4,
                    cls=ObjectEncoder),
                    content_type='application/json;charset=utf-8',
                    status=202)
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    #############################SEARCH EACH PRODUCTS####################################################################################
    @http.route(['/api/search/product'], auth="public", type='http', csrf=False)
    def search_product(self, token=None, **kw):
        product_list_category = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        product_id = request.env['product.product'].sudo().search(
            [('id', '=', int(kw.get('product_id')))])
        partner_id = request.env['res.partner'].sudo().search(
            [('id', '=', int(kw.get('partner_id')))])
        try:
            flag = False
            if uid:
                if product_id:
                    if partner_id:
                        if partner_id.property_product_pricelist:
                            for rec in partner_id.property_product_pricelist.item_ids:
                                if rec.id == product_id.id:
                                    dic = {
                                        'id': rec.product_tmpl_id.id if rec.product_tmpl_id.id else None,
                                        'name': rec.product_tmpl_id.name if rec.product_tmpl_id.name else None,
                                        'product_type': rec.product_tmpl_id.detailed_type if rec.product_tmpl_id.detailed_type else None,
                                        'product_category': rec.product_tmpl_id.categ_id.id if rec.product_tmpl_id.categ_id else None,
                                        'product_image': rec.product_tmpl_id.image_url,
                                        'arabic_name': rec.product_tmpl_id.name_arabic,
                                        'product_code': rec.product_tmpl_id.product_code,
                                        'product_amount': "{:.3f}".format(
                                            rec.product_tmpl_id.product_amount),
                                        'product_discount': rec.product_tmpl_id.product_discount,
                                        'product_price': "{:.3f}".format(rec.fixed_price),
                                        'box': rec.product_tmpl_id.box,
                                        'bag': rec.product_tmpl_id.bag,
                                        'description': rec.product_tmpl_id.description_sale,
                                        'onhand_qty': rec.product_tmpl_id.qty_available
                                    }
                                    product_list_category.append(dic)
                                    flag = True
                            if not flag:
                                dic = {
                                    'id': product_id.id if product_id.id else None,
                                    'name': product_id.name if product_id.name else None,
                                    'product_type': product_id.detailed_type if product_id.detailed_type else None,
                                    'product_category': product_id.categ_id.id if product_id.categ_id else None,
                                    'product_image': product_id.image_url,
                                    'product_code': product_id.product_code,
                                    'product_amount': "{:.3f}".format(product_id.product_amount),
                                    'product_discount': product_id.product_discount,
                                    'product_price': "{:.3f}".format(product_id.list_price),
                                    'box': product_id.id,
                                    'bag': product_id.id,
                                    'description': product_id.description_sale,
                                    'onhand_qty': product_id.qty_available
                                }
                                product_list_category.append(dic)

                        return Response(json.dumps(
                            {"data": product_list_category,
                             'message': 'Success', 'success': True},
                            sort_keys=True, indent=4, cls=ObjectEncoder),
                            content_type='application/json;charset=utf-8',
                            status=200)
                    else:
                        return Response(json.dumps(
                            {"data": None, 'message': 'Partner not found',
                             'success': False}, sort_keys=True, indent=4,
                            cls=ObjectEncoder),
                            content_type='application/json;charset=utf-8',
                            status=202)
                else:
                    return Response(json.dumps(
                        {"data": None, 'message': 'Category not found',
                         'success': False}, sort_keys=True, indent=4,
                        cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)
            else:
                return Response(json.dumps(
                    {"data": None, 'message': 'Token authentication failed',
                     'success': False}, sort_keys=True, indent=4,
                    cls=ObjectEncoder),
                    content_type='application/json;charset=utf-8',
                    status=202)
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ########################################################################################################################
    @http.route([
        '/api/search/product/categories'], auth="public", type='http',
        csrf=False)
    def search_product_categories(self, token=None, **kw):
        product_list = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        user_id = kw.get('user_id')
        try:
            if uid:
                user = request.env['res.users'].sudo().search(
                    [("id", "=", user_id)])
                if user.category:
                    categories = user.category
                    if categories:
                        product_categories = request.env['product.category'].sudo().search(
                            [('parent_id', 'in', categories.ids)])

                else:
                    product_categories = request.env[
                        'product.category'].sudo().search([])

                if product_categories:
                    for i in product_categories:
                        dic = {
                            'id': i.id if i.id else None,
                            'name': i.name if i.name else None,
                            'img_url': i.img_url if i.img_url else None
                        }
                        product_list.append(dic)
                    msg = "Success"
                    success = True
                    return Response(json.dumps(
                        {"data": product_list, 'message': msg,
                         'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "Failed"
                    success = False
                    result = None
                    return Response(json.dumps(
                        {"data": result, 'message': msg, 'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)

            msg = "Token authentication failed"
            success = False
            result = None
            return Response(
                json.dumps({"data": result, 'message': msg, 'success': success},
                           sort_keys=True, indent=4, cls=ObjectEncoder),
                content_type='application/json;charset=utf-8', status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    #################################ALL PRODUCTS#########################################

    @http.route([
        '/api/search/all/products'], auth="public", type='http', csrf=False)
    def search_all_products(self, token=None, **kw):
        product_list = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        user_id = kw.get('user_id')
        try:
            if uid:
                user = request.env['res.users'].sudo().search(
                    [("id", '=', int(user_id))])
                categ =user.category.ids
                read_group_res = request.env['product.template'].sudo().read_group(
                    [('categ_id', 'child_of', categ)], ['categ_id'], ['categ_id'])
                categorys = [data['categ_id'][0] for data in read_group_res]
                if categ:
                    products = request.env['product.product'].sudo().search(
                        [('categ_id', 'in', categorys)])
                else:
                    products = request.env['product.product'].sudo().search([])
                if products:
                    location_product = request.env['stock.quant'].sudo().search([('product_id', 'in', products.ids),('location_id.branch_id','=',user.branch_id.id)])
                    for i in location_product:
                        dic = {
                            'id': i.product_id.id if i.product_id else None,
                            'name': i.product_id.name if i.product_id else None,
                            'product_code': i.product_id.product_tmpl_id.product_code,
                            'price': "{:.3f}".format(i.product_id.product_tmpl_id.list_price),
                            'box': i.product_id.product_tmpl_id.box,
                            'bag': i.product_id.product_tmpl_id.bag,
                            'onhand_qty': i.quantity
                        }
                        product_list.append(dic)
                    msg = "Success"
                    success = True
                    return Response(json.dumps(
                        {"data": product_list, 'message': msg,
                         'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "Failed"
                    success = False
                    result = None
                    return Response(json.dumps(
                        {"data": result, 'message': msg, 'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)
            else:
                msg = "Token authentication failed"
                success = False
                result = None
                return Response(json.dumps(
                    {"data": result, 'message': msg, 'success': success},
                    sort_keys=True, indent=4, cls=ObjectEncoder),
                    content_type='application/json;charset=utf-8',
                    status=202)
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ############# SALE ORDER FOR IDEA ###############
    @http.route(['/api/create/sale/order/<string:token>/'], auth="public",
                methods=['POST'], type='json', csrf=False)
    def create_sale_order(self, token, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            if uid:
                partner = request.env['res.partner'].sudo().search(
                    [('id', '=', int(data['partner_id']))])
                print(partner, "1")
                sale_order = request.env['sale.order'].sudo().search(
                    [('partner_id', '=', partner.id), ('state', '=', 'draft'),
                     ('sale_return', '=', False)], limit=1)
                print(sale_order, "2")
                if not sale_order:
                    team_id = request.env['crm.team'].search(
                        [('user_id', '=', int(data['user_id']))], limit=1)
                    sale_order = request.env['sale.order'].sudo().create({
                        'sale_return': False,
                        'api_divider': True,
                        'team_id': team_id.id,
                        'partner_id': partner.id,
                        'state': 'draft',
                        'workflow_process_id': 1,
                        'user_id': partner.user_id.id,
                    })
                else:
                    sale_order = sale_order
                    print(sale_order, "3")
                product_lines = data['product_ids']
                print(product_lines, "4")
                for prod in product_lines:
                    product_product = request.env['product.product'].sudo().browse(int(prod['id'])).exists()
                    if product_product:
                        order_lines = request.env['sale.order.line'].sudo().create({
                            'product_id': product_product.id,
                            # 'price_unit': prod['unit_price'],
                            'product_uom_qty': prod['product_qty'],
                            'order_id': sale_order.id,
                        })
                    else:
                        return {'status': 202, 'message': 'Product not found'}
                    # print(prod, "//////////////////////////////////////////")
                    # if request.env['sale.order.line'].sudo().search([('order_id.id', '=', sale_order.id), ('product_id.id', '=', int(prod['id']))]):
                    #     print("ddddddddddddddddd")
                    #     return {'status': 202, 'message': 'Already In Cart'}
                    # else:
                    #     print("e;see")
                    #     order_lines = request.env['sale.order.line'].sudo().create({
                    #         'product_id': prod['id'],
                    #         # 'price_unit': prod['unit_price'],
                    #         'product_uom_qty': prod['product_qty'],
                    #         'order_id': sale_order.id,
                    #     })
                # sale_order.action_run_workflow()
                return {'status': 200,
                        'message': 'Sale order created successfully.',
                        'order_id': sale_order.id,
                        'zone': sale_order.team_id.name,
                        'branch': sale_order.branch_id.name}
            else:
                return {'status': 202, 'message': 'Token Expired'}

        except KeyError as key_error:
            return {'status': 202,
                    'message': f"Missing required parameter: {str(key_error)}"}

        except Exception as error:
            _logger.error(error)
            return {'status': 400, 'message': 'An error occurred during sale order creation.'}

    #######################################cart show#####################################
    @http.route(['/api/cart/show'], auth="public", type='http', csrf=False)
    def cart_show(self, token=None, **kw):
        cart_list = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        partner_id = request.env['res.partner'].sudo().search(
            [('id', '=', int(kw.get('partner_id')))])
        flag = 0
        try:
            if uid and partner_id:
                if partner_id:
                    carts = request.env['sale.order'].sudo().search(
                        [('partner_id', '=', int(partner_id)), ('state', '=', 'draft')], limit=1)
                    if carts:
                        untaxed = 0
                        for data in carts.order_line:
                            # print(partner_id.property_product_pricelist.item_ids, "data")
                            # for rec in partner_id.property_product_pricelist.item_ids:
                            #     if rec.product_tmpl_id.id == data.product_id.id:
                            #         dic = {
                            #             # 'cart_id': carts.id,
                            #             'product_id': data.product_id.id,
                            #             'name': data.product_id.name,
                            #             'box': data.product_id.product_tmpl_id.box,
                            #             'bag': data.product_id.product_tmpl_id.bag,
                            #             'description': data.product_id.description_sale,
                            #             'onhand_qty': data.product_id.qty_available,
                            #             'line_id': data.id,
                            #             'product_subtotal': "{:.3f}".format(data.price_subtotal),
                            #             'product_amount': "{:.3f}".format(data.product_id.product_amount),
                            #             'product_discount': data.product_id.product_discount,
                            #             'product_price': "{:.3f}".format(rec.fixed_price),
                            #             'image': data.product_id.image_url,
                            #             'product_code': data.product_id.product_code,
                            #             'qty': data.product_uom_qty,
                            #             'unit_price': "{:.3f}".format(data.price_unit),
                            #             # 'untaxed': carts.amount_untaxed,
                            #             # 'tax': carts.amount_tax,
                            #             # 'cart_discount': carts.universal_total_display_discount_amount,
                            #             # 'total_amount': carts.amount_total,
                            #
                            #         }
                            #         cart_list.append(dic)
                            #         flag = 1
                            # if flag == 0:
                            dic = {
                                # 'cart_id': carts.id,
                                'product_id': data.product_id.id,
                                'name': data.product_id.name,
                                'box': data.product_id.product_tmpl_id.box,
                                'bag': data.product_id.product_tmpl_id.bag,
                                'description': data.product_id.description_sale,
                                'onhand_qty': data.product_id.qty_available,
                                'line_id': data.id,
                                'product_subtotal': "{:.3f}".format(data.price_subtotal),
                                'product_amount': "{:.3f}".format(data.product_id.product_amount),
                                'product_discount': data.product_id.product_discount,
                                'product_price': "{:.3f}".format(data.product_id.list_price),
                                'image': data.product_id.image_url,
                                'product_code': data.product_id.product_code,
                                'qty': data.product_uom_qty,
                                'unit_price': "{:.3f}".format(data.price_unit),
                                "foc": "0",
                                # 'untaxed': carts.amount_untaxed,
                                # 'tax': carts.amount_tax,
                                # 'cart_discount': carts.universal_total_display_discount_amount,
                                # 'total_amount': carts.amount_total,

                            }
                            cart_list.append(dic)
                            untaxed += data.price_subtotal
                        msg = "Success"
                        success = True
                        return Response(json.dumps(
                            {"data": cart_list, 'message': msg,
                             'success': success, 'cart_id': carts.id,
                             'untaxed_amount': untaxed,
                             'tax': carts.amount_tax,
                             'narration': carts.narration if carts.narration else None,
                             'cart_discount': carts.universal_discount_rate,
                             'total_amount': "{:.3f}".format(carts.amount_total),
                             'discount_amount': "{:.3f}".format(
                                 carts.universal_total_display_discount_amount)},
                            sort_keys=True, indent=4, cls=ObjectEncoder),
                            content_type='application/json;charset=utf-8',
                            status=200)
                    else:
                        msg = "Failed"
                        success = False
                        result = None
                        return Response(json.dumps(
                            {"data": result, 'message': msg,
                             'success': success},
                            sort_keys=True, indent=4, cls=ObjectEncoder),
                            content_type='application/json;charset=utf-8',
                            status=202)

            else:
                if not partner_id:
                    msg = "PRODUCT ID is null"
                if not uid:
                    msg = "Token authentication failed"
            success = False
            result = None
            return Response(
                json.dumps({"data": result, 'message': msg, 'success': success},
                           sort_keys=True, indent=4, cls=ObjectEncoder),
                content_type='application/json;charset=utf-8', status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ##################################DELETE CART ITEMS###############################################
    @http.route(['/api/delete/cart/items/'], auth="public", type='http', csrf=False)
    def delete_cart_items(self, token=None, **kw):
        try:
            data = json.loads(request.httprequest.data)
            ensure_db()
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(data['token'])
            line_id = data['line_id']
            if uid and line_id:
                order_line = request.env['sale.order.line'].sudo().search(
                    [('id', '=', int(line_id))])
                if order_line:
                    order_line.unlink()
                    return Response(json.dumps(
                        {"status": 200, 'message': "Successfully Unlinked"}))
                else:
                    return Response(json.dumps(
                        {"status": 202, 'message': "No lines In The System"}))
            else:
                if not uid:
                    body = "Token Expired"
                if not line_id:
                    body = "Product Id Is Null"
                return Response(json.dumps({"status": 202, 'message': body}))
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ####################################DELETE CART########################################

    @http.route(['/api/delete/cart/<string:token>/'], auth="public", type='http', csrf=False)
    def delete_cart(self, token, cart_id=False, **kw):
        try:
            ensure_db()
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            if uid and cart_id:
                order = request.env['sale.order'].sudo().search(
                    [('id', '=', int(cart_id))])
                if order:
                    order.unlink()
                    return Response(json.dumps(
                        {"status": 200, 'message': "Successfully Unlinked"}))
                else:
                    return Response(json.dumps(
                        {"status": 202, 'message': "No Record In The System"}))
            else:
                if not cart_id:
                    body = "Cart Id Is Null"
                if not uid:
                    body = "Token Expired"
                return Response(json.dumps({"status": 202, 'message': body}))
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    @http.route(['/api/product/update/'], auth="public", type='json', csrf=False, methods=['POST'])
    def add_pro_cart(self, token=None, **kw):
        try:
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(data['token'])
            if uid and data:
                order_line = request.env['sale.order.line'].sudo().search(
                    [('id', '=', int(data['line_id']))])
                if order_line:
                    if data['image']:
                        order_line.write({
                            'image_url': data['image']
                        })
                    if data['qty']:
                        order_line.write({
                            'product_uom_qty': int(data['qty'])
                        })
                    return {'status': 200, 'message': "Successfully Updated"}
                else:
                    return {'status': 202, 'message': "This Product Not In The System"}
            else:
                if not uid:
                    body = "Token Expired "
                if not data:
                    body = "Data Is Null "
                return {'status': 202, 'message': body}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    #########################################Getting the products###############################################################################

    @http.route([
        '/api/sale/return/product/list/'], auth="public", type='http', csrf=False)
    def sale_return_product_list(self, token=False, **kw):
        try:
            ensure_db()
            # data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            partner = int(kw.get('partner'))
            partner_id = request.env['res.partner'].sudo().browse(partner)
            product_list = []
            if uid and partner_id:
                orders = request.env['sale.order'].sudo().search(
                    [('partner_id', '=', partner_id.id), ('state', '=', 'sale'),
                     ('sale_return', '=', False)])
                if orders:
                    for rec in orders:
                        for pick in rec.picking_ids:
                            if pick.state == 'done':
                                for line in rec.order_line:
                                    product_qty = line.product_uom_qty - line.return_qty
                                    if product_qty > 0:
                                        dic = {
                                            'product_id': line.product_id.id,
                                            'product_qty': product_qty,
                                            'product_name': line.product_id.name,
                                            'product_code': line.product_id.product_code,
                                            'order_id': rec.id,
                                            'order_name': rec.name,
                                            'line_id': line.id,
                                        }
                                        product_list.append(dic)
                                break
                else:
                    return Response(json.dumps({"status": 202, 'message': "No User With This Id"}))
                if product_list:
                    return Response(
                        json.dumps({"data": product_list, 'message': "Success",
                                    'success': True}, sort_keys=True,
                                   indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    return Response(json.dumps(
                        {"status": 202, 'message': "No Product In Cart"}))
            else:
                if not partner_id:
                    body = "Partner Id Is Null"
                if not uid:
                    body = "Token Expired"
                return Response(json.dumps({"status": 202, 'message': body}))
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ########################################SALE RETURN FOR IDEA########################################
    @http.route(['/api/create/sale/return/<string:token>/'], auth="public",
                methods=['POST'], type='json', csrf=False)
    def create_sale_return(self, token, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            if uid:
                partner = request.env['res.partner'].sudo().search(
                    [('id', '=', int(data['partner_id']))])
                
                sale_return = request.env['sale.order'].sudo().create({
                    'partner_id': partner.id,
                    'state': 'draft',
                    'sale_return': True,
                })
                product_lines = data['product_ids']
                for prod in product_lines:
                    product = request.env['product.product'].sudo().browse(prod['id'])
                    order_lines = request.env['sale.order.line'].sudo().create({
                        'product_id': prod['id'],
                        # 'price_unit': prod['unit_price'],
                        'product_uom_qty': prod['product_qty'],
                        'order_id': sale_return.id,
                        'return_line_id': prod['line_id'],
                    })

                    lines = request.env['sale.order.line'].sudo().search([('id', '=', int(prod['line_id']))])
                    lines.return_qty += float(prod['product_qty'])
                return {'status': 200,
                        'message': 'Sale Return Created successfully.',
                        'order_id': sale_return.id}
            else:
                return {'status': 202, 'message': 'Token Expired'}
        except KeyError as key_error:
            return {'status': 202,
                    'message': f"Missing required parameter: {str(key_error)}"}
        except Exception as error:
            _logger.error(error)
            return {'status': 400,
                    'message': 'An error occurred during sale return creation.'}

    ####################################RECENT ORDERS########################################################
    @http.route('/api/recent/orders', auth="public", methods=['GET'], type='http', csrf=False)
    def recent_recent_orders(self, token=None, **kw):
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        user_id = kw.get('user_id')
        try:
            if uid:
                domains = []
                if user_id:
                    domains.append(('user_id', '=', int(user_id)))
                sale_orders = request.env['sale.order'].sudo().search(
                    [('state', '=', 'sale'), ('user_id', '=', int(user_id))])
                recent_orders = []
                if uid:
                    for i in sale_orders:
                        order_lines = []
                        total_product_qty = 0
                        total_price = 0
                        for j in i.order_line:
                            product_qty = j.product_uom_qty if j.product_uom_qty else 0
                            total = j.price_unit if j.price_unit else 0
                            total_product_qty += product_qty
                            total_price += total
                        order_line_dic = {
                            'total_qty': total_product_qty,
                            # 'total_value':"{:.3f}".format(total_price)
                        }
                        order_lines.append(order_line_dic)

                        order_dic = {
                            'create_date': i.date_order.date().isoformat() if i.date_order else None,
                            'order_name': i.name if i.name else None,
                            'order_id': i.id,
                            'partner_id': i.partner_id.id,
                            'partner_name': i.partner_id.name if i.partner_id else None,
                            'order_line': order_lines,
                            'total_value': "{:.3f}".format(i.amount_total),
                            # 'status':i.state
                        }
                        recent_orders.append(order_dic)
                    if recent_orders:
                        msg = "Success"
                        success = True
                        return Response(json.dumps(
                            {"data": recent_orders, 'message': msg,
                             'success': success},
                            sort_keys=True, indent=4, cls=ObjectEncoder),
                            content_type='application/json;charset=utf-8',
                            status=200)
                    else:
                        msg = "No recent orders found"
                        success = False
                        return Response(json.dumps(
                            {"data": None, 'message': msg, 'success': success},
                            sort_keys=True, indent=4, cls=ObjectEncoder),
                            content_type='application/json;charset=utf-8',
                            status=202)
                else:
                    msg = "Token authentication failed"
                    success = False
                    return Response(json.dumps(
                        {"data": None, 'message': msg, 'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ###############################search each orders##################################################
    @http.route([
        '/api/search/order'], auth="public", type='http', csrf=False)
    def search_order_search(self, token=None, **kw):
        orders = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        order_id = kw.get('order_id')
        try:
            if uid and order_id:
                if order_id:
                    order_list = request.env['sale.order'].sudo().search(
                        [('id', '=', int(order_id))])
                    if order_list:
                        total_product_qty = 0
                        untaxed_total = 0
                        for line in order_list.order_line:
                            # line.product_qty_sum += line.product_uom_qty
                            untaxed_total += line.price_subtotal
                            total_product_qty += line.product_uom_qty
                            # total_product_qty += line.product_uom_qty
                            dic = {
                                # 'id':orders.id,
                                'product_id': line.product_id.id,
                                'product_name': line.product_id.name,
                                'description': line.product_id.description_sale,
                                'product_subtotal': "{:.3f}".format(line.price_subtotal),
                                'product_amount': "{:.3f}".format(line.product_id.product_tmpl_id.product_amount),
                                'product_price': "{:.3f}".format(line.price_unit),
                                'product_qty': line.product_uom_qty,
                                'product_discount': line.product_id.product_tmpl_id.product_discount,
                                'product_image': line.product_id.image_url,
                                'product_code': line.product_id.product_code,
                                'line_id': line.id
                            }
                            orders.append(dic)
                        dict_1 = {
                            'id': order_list.id,
                            'order_name': order_list.invoice_ids.name,
                            'partner_id': order_list.partner_id.id,
                            'partner_name': order_list.partner_id.name,
                            'address': order_list.partner_id.street,
                            'order_discount': order_list.universal_total_display_discount_amount,
                            'discount_rate': int(order_list.universal_discount_rate),
                            'total_amount': "{:.3f}".format(order_list.amount_total),
                            'sub_total': "{:.3f}".format(untaxed_total),
                            'tax': "{:.3f}".format(order_list.amount_tax),
                            'mobile': order_list.partner_id.mobile,
                            'phone': order_list.partner_id.phone,
                            'email': order_list.partner_id.email,
                            'total_qty': total_product_qty,
                            'date': str(order_list.date_order),
                            'line_ids': orders,
                        }
                        # orders.append(dic)
                        msg = "Success"
                        success = True
                        return Response(json.dumps(
                            {"data": dict_1, 'message': msg,
                             'success': success},
                            sort_keys=True, indent=4, cls=ObjectEncoder),
                            content_type='application/json;charset=utf-8',
                            status=200)
                else:
                    msg = "Failed"
                    success = False
                    result = None
                    return Response(json.dumps(
                        {"data": result, 'message': msg, 'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)

            else:
                if not order_id:
                    msg = "ORDER ID is null"
                if not uid:
                    msg = "Token authentication failed"
            success = False
            result = None
            return Response(
                json.dumps({"data": result, 'message': msg, 'success': success},
                           sort_keys=True, indent=4, cls=ObjectEncoder),
                content_type='application/json;charset=utf-8', status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    #######################################Search Sales Person and Customers#################################################

    @http.route([
        '/api/search/salesperson/customers'], auth="public", type='http',
        csrf=False)
    def search_all(self, token=None, **kw):
        person_list = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        partner_id = kw.get('partner_id')
        user_id = kw.get('user_id')
        try:
            if user_id and partner_id and uid:
                person = request.env['sale.order'].sudo().search(
                    [('partner_id', '=', int(partner_id)),
                     ('user_id', '=', int(user_id)),
                     ('state', 'in', ('sale', 'done'))])
                if person:
                    for data in person:
                        invoice = request.env['account.move'].sudo().search(
                            [('invoice_origin', '=', data.name)], limit=1)
                        date_order_formatted = data.date_order.strftime(
                            '%Y-%m-%d %H:%M:%S') if data.date_order else None
                        dic = {
                            'id': data.id,
                            'name': data.name,
                            'partner_id': data.partner_id.id,
                            'partner_name': data.partner_id.name,
                            'date_order': date_order_formatted,
                            'mobile': data.partner_id.mobile,
                            'email': data.partner_id.email,
                            'street': data.partner_id.street,
                            'amount_due': "{:.3f}".format(invoice.amount_residual),
                            'total': "{:.3f}".format(data.amount_total),
                            'sale_due': "{:.3f}".format(data.amount_total - invoice.amount_residual)
                        }
                        person_list.append(dic)
                    msg = "Success"
                    success = True
                    return Response(json.dumps(
                        {"data": person_list, 'message': msg,
                         'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "No Sale Against This User"
                    success = False
                    result = None
                    return Response(json.dumps(
                        {"data": result, 'message': msg, 'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)

            else:
                if not partner_id:
                    msg = "PARTNER ID is null"
                if not uid:
                    msg = "Token authentication failed"
            success = False
            result = None
            return Response(
                json.dumps({"data": result, 'message': msg, 'success': success},
                           sort_keys=True, indent=4, cls=ObjectEncoder),
                content_type='application/json;charset=utf-8', status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ########################################order confimation########################################################
    @http.route(['/api/order/confirmation/<string:token>/'], auth="public",
                methods=['POST'], type='json', csrf=False)
    def search_order_confirmation(self, token=None, **kw):
        try:
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            if uid:
                partner = request.env['res.partner'].sudo().search(
                    [('id', '=', int(data['partner_id']))])
                orders = request.env['sale.order'].sudo().search(
                    [('id', '=', int(data['order_id']))])
                # if int(data['universal_discount_rate']):
                #     disc = orders.write({
                #         'universal_discount_enable': True,
                #         'universal_discount_type': 'percent',
                #         'universal_discount_rate': int(
                #             data['universal_discount_rate']),
                #     })
                #     orders._compute_amounts()

                # orders.tax_calculation_button()
                # print(tax, 'taaxxxxxxxxxxxxxxxxxxxx')
                # orders_list = []
                # for rec in orders:
                #     dic1={
                #         'universal_discount_enable':True,
                #         'universal_discount_type':'percent',
                #         'discount':int(data['universal_discount_rate'])
                #
                #     }
                #     orders_list.append(dic1)
                # for data in orders:
                #     dic = {
                #         'id': orders.id,
                #         'partner_id':partner.id
                #                 # 'order_name':order.name
                #     }
                #     orders_list.append(dic)
                #     print(orders_list,'orderrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr')
                # automatic = request.env['automatic.workflow.job']
                # work_flow = automatic.run(int(data['order_id']))
                # if work_flow:
                #     orders.action_unlock()
                #     invoice = request.env['account.move'].sudo().search(
                #         [('invoice_origin', '=', orders.name),
                #          ('state', '=', 'draft')], limit=1)
                #     if invoice:
                #         invoice.action_post()
                if orders:
                    if partner.customer_credit_limit < orders.amount_total:
                        return {'status': 202,
                                'message': 'Customer credit limit exceeded',
                                'order_id': orders.id}
                    else:
                        orders.narration = data['narration']
                        orders.sudo().action_run_workflow()
                        orders.invoice_ids.sudo().action_post()
                        success = True
                        return {'status': 200,
                                'message': 'Order Confirmed successfully.','success':success,
                                'order_id': orders.id}
                else:
                    msg = "Failed"
                    success = False
                    result = None
                    return Response(json.dumps(
                        {"data": result, 'message': msg, 'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)
            else:
                return {'status': 202, 'message': 'Token Expired'}

        except KeyError as key_error:
            return {'status': 202,
                    'message': f"Missing required parameter: {str(key_error)}"}

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ##########################################Payment 1st API (Customer invoice)#########################################################

    @http.route([
        '/api/search/customer/invoice'], auth="public", type='http', csrf=False)
    def search_all_invoice(self, token=None, **kw):
        partner_list = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        partner_id = int(kw.get('partner_id'))
        partners = request.env['res.partner'].sudo().search([('id', '=', partner_id)])
        try:
            if partner_id and uid:
                partner = request.env['account.move'].sudo().search(
                    [('partner_id', '=', int(partner_id)),
                     ('payment_state', '!=', 'paid'),
                     ('move_type', '=', 'out_invoice')])
                if partner:
                    over_due = 0
                    amount_due = 0
                    amount_totals = 0
                    for i in partner:
                        amount_totals += i.amount_total
                        due_day = i.due_days
                        invoice_date = i.invoice_date
                        due_date = invoice_date + timedelta(days=int(due_day))
                        # if due_date >= datetime.today():
                        due_date_datetime = datetime.combine(due_date,
                                                             datetime.min.time())
                        if due_date_datetime <= datetime.now():
                            amount_due += i.amount_residual
                        else:
                            over_due += i.amount_residual
                    dic = {
                        # 'id': data.id,
                        'name': i.partner_id.name if i.partner_id.name else None,
                        'street': i.partner_id.street if i.partner_id.street else None,
                        'street2': i.partner_id.street2 if i.partner_id.street2 else None,
                        'city': i.partner_id.city if i.partner_id.city else None,
                        'state': i.partner_id.state_id.id if i.partner_id.state_id else None,
                        'country': i.partner_id.country_id.id if i.partner_id.country_id else None,
                        'zip': i.partner_id.zip if i.partner_id.zip else None,
                        'phone': i.partner_id.phone if i.partner_id.phone else None,
                        'email': i.partner_id.email if i.partner_id.email else None,
                        # 'partner_id': data.partner_id.id,
                        'due': "{:.3f}".format(amount_due),
                        'over_due': "{:.3f}".format(over_due),
                        'total_amount': "{:.3f}".format(over_due + amount_due),
                        # 'total_due':
                    }
                    partner_list.append(dic)
                    msg = "Success"
                    success = True
                    return Response(json.dumps(
                        {"data": partner_list, 'message': msg,
                         'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    dic = {
                        # 'id': data.id,
                        'name': partners.name,
                        'street': partners.street if partners.street else None,
                        'street2': partners.street2 if partners.street2 else None,
                        'city': partners.city if partners.city else None,
                        'state': partners.state_id.id if partners.state_id else None,
                        'country': partners.country_id.id if partners.country_id else None,
                        'zip': partners.zip if partners.zip else None,
                        'phone': partners.phone if partners.phone else None,
                        'email': partners.email if partners.email else None,
                        # 'partner_id': data.partner_id.id,
                        'due': "{:.3f}".format(0),
                        'over_due': "{:.3f}".format(0),
                        'total_amount': "{:.3f}".format(0),
                        # 'total_due':
                    }
                    partner_list.append(dic)
                    msg = "No Sale Against This User"
                    success = False
                    result = None
                    return Response(json.dumps(
                        {"data": partner_list, 'message': msg, 'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)

            else:
                if not partner_id:
                    msg = "PARTNER ID is null"
                if not uid:
                    msg = "Token authentication failed"
            success = False
            result = None
            return Response(
                json.dumps({"data": result, 'message': msg, 'success': success},
                           sort_keys=True, indent=4, cls=ObjectEncoder),
                content_type='application/json;charset=utf-8', status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    #################################################Discount Apply API(updation)##################################################################

    @http.route(['/api/apply/sale/discount/<string:token>/'], auth="public",
                methods=['POST'], type='json', csrf=False)
    def apply_sale_discount(self, token, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            if uid:
                sale_orders = request.env['sale.order'].sudo().search(
                    [('id', '=', int(data['order_id'])),
                     ('state', '=', 'draft')], limit=1)
                if sale_orders:
                    sale_orders.write({
                        'universal_discount_enable': True,
                        'universal_discount_type': 'percent',
                        'id': int(data['order_id']),
                        'universal_discount_rate': float(data['discount_rate'])
                    })
                    sale_orders._compute_amounts()

                    # sale_orders.write({
                    #
                    #     'ks_global_tax_rate': 5.0
                    # })
                    # sale_orders._compute_amounts()
                    # print(sale_orders.ks_global_tax_rate,
                    #       'printttttttttttttttttttttttttttttttttttttttttttttttttttt')

                    # untaxed= sale_orders.amount_untaxed
                    # taxed = sale_orders.amount_tax
                    # total = untaxed + taxed
                    # discount = sale_orders.univresal_discount_rate
                    # final_total = total - discount

                    return {'status': 200,
                            'message': 'Discount Applied successfully.',
                            'order_id': sale_orders.id,
                            'untaxed': sale_orders.amount_untaxed,
                            'amount_taxed': sale_orders.amount_tax,
                            'total': sale_orders.amount_total}
                else:
                    return {'status': 404, 'message': 'Sale Order Not Exist.'}
            else:
                return {'status': 202, 'message': 'Token Expired'}

        except KeyError as key_error:
            return {'status': 202,
                    'message': f"Missing required parameter: {str(key_error)}"}

        except Exception as error:
            _logger.error(error)
            return {'status': 400,
                    'message': 'An error occurred during Applying Discount.'}

    ###################################################################################################################

    @http.route('/api/authenticate/refresh', auth="none", type='json',
                methods=['POST'], csrf=False)
    def api_authenticate_refresh(self, **kw):
        try:
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].refresh_token(data['token'])
            if uid:
                return {'status': 200, 'message': "Success ", 'body': uid}
            else:
                return {'status': 202, 'message': "Token Not In The System"}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    # recent API

    ##################ANAGHA.V.P API STARTING FROM HERE####
    ########################################### POS VIEW ALL INVOICE DETAILS #######################################

    @http.route(['/api/pointofsale/all/invoice'], auth="none", type='http',
                csrf=False)
    def pos_all_invoice(self, token, **kwargs):
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        invoice = request.env['account.move'].sudo().search(
            [('state', '=', 'posted')])
        print(invoice, "invoicesssss")
        try:
            if uid:
                invoice = request.env['account.move'].sudo().search(
                    [('state', '=', 'posted')])
                print(invoice, "invoices")
                invoice_list = []
                if invoice:
                    for rec in invoice:
                        for res in rec.invoice_line_ids:
                            date_invoiced = None
                            if rec.invoice_date:
                                date_invoiced = rec.invoice_date.strftime('%Y-%m-%d')
                            dic = {
                                'id': rec.id if rec.id else None,
                                'display_name': rec.display_name if rec.display_name else None,
                                'partner_id': rec.partner_id.id if rec.partner_id else None,
                                'team_id': rec.team_id.id if rec.team_id else None,
                                'invoice_date': date_invoiced,
                                'branch_id': rec.branch_id.id if rec.branch_id else None,
                                'product_id': res.product_id.id if res.product_id else None,
                                'account_id': res.account_id.id if res.account_id else None,
                                'quantity': res.quantity if res.quantity else None,
                                'price_unit': "{:.3f}".format(
                                    res.price_unit) if res.price_unit else None,
                                'price_subtotal': "{:.3f}".format(
                                    res.price_subtotal) if res.price_subtotal else None,
                                'amount_total_signed': "{:.3f}".format(
                                    rec.amount_total_signed) if rec.amount_total_signed else None,
                            }
                            invoice_list.append(dic)
                    return Response(
                        json.dumps({'data': invoice_list}, sort_keys=True,
                                   indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "Undefined invoices"
                    success = False
                    return {'status': 200, 'message': msg, 'success': success,
                            'body': uid}
            else:
                return {'status': 202, 'message': 'Token Expired'}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

            # @http.route(['/api/pointofsale/all/invoice'], auth="none", type='http',

    #             csrf=False)
    # def pos_all_invoice(self, token, **kwargs):
    #     print(request.env['account.move'].sudo().search([('state', '=', 'posted')]),
    #           "Selfffffff")
    #     ensure_db()
    #     env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
    #     uid = env['sfk_rest.token'].check_token(token)
    #     invoice = request.env['account.move'].sudo().search(
    #         [('state', '=', 'posted')])
    #     print(invoice, "invoicesssss")
    #     try:
    #         if uid:
    #             invoice = request.env['account.move'].sudo().search(
    #                 [('state', '=', 'posted')])
    #             print(invoice, "invoices")
    #             invoice_list = []
    #             if invoice:
    #                 for rec in invoice:
    #                     for res in rec.invoice_line_ids:
    #                         # date_1 = rec.invoice_date.strftime('%Y-%m-%d')
    #                         date_invoiced = rec.invoice_date.strftime('%Y-%m-%d') if isinstance(rec.invoice_date,
    #                                                                                             datetime) else None
    #                         dic = {
    #                             'id': rec.id if rec.id else None,
    #                             'display_name': rec.display_name if rec.display_name else None,
    #                             'partner_id': rec.partner_id.id if rec.partner_id else None,
    #                             'team_id': rec.team_id.id if rec.team_id else None,
    #                             'invoice_date': date_invoiced if date_invoiced else None,
    #                             'branch_id': rec.branch_id.id if rec.branch_id else None,
    #                             'product_id': res.product_id.id if res.product_id else None,
    #                             'account_id': res.account_id.id if res.account_id else None,
    #                             'quantity': res.quantity if res.quantity else None,
    #                             'price_unit': res.price_unit if res.price_unit else None,
    #                             'price_subtotal': res.price_subtotal if res.price_subtotal else None,
    #                             'amount_total_signed': rec.amount_total_signed if rec.amount_total_signed else None,
    #                         }
    #                         invoice_list.append(dic)
    #                 return Response(
    #                     json.dumps({'data': invoice_list}, sort_keys=True,
    #                                indent=4, cls=ObjectEncoder),
    #                     content_type='application/json;charset=utf-8',
    #                     status=200)
    #             else:
    #                 msg = "Undefined invoices"
    #                 success = False
    #                 return {'status': 200, 'message': msg, 'success': success,
    #                         'body': uid}
    #         else:
    #             return {'status': 202, 'message': 'Token Expired'}
    #     except Exception as error:
    #         print("22222222222222")
    #         _logger.error(error)
    #         abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ########################################### POS VIEW CUSTOMER FILTER BY SALES PERSON #######################################

    # @http.route(['/api/pointofsale/all/customer/filter/sales/person'], auth="none", type='http',
    #             csrf=False)
    # def pos_all_customer_filter(self, token, **kw):
    #     ensure_db()
    #     env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
    #     uid = env['sfk_rest.token'].check_token(token)
    #     salesperson = kw.get('salesperson_id')
    #     try:
    #         if uid:
    #             # if team:
    #             customer = request.env['res.partner'].sudo().search([('user_id.id', '=', salesperson)])
    #             customer_list = []
    #             if customer:
    #                 for rec in customer:
    #                     dic = {
    #                         'id': rec.id if rec.id else None,
    #                         'name': rec.name if rec.name else None,
    #                         'street': rec.street if rec.street else None,
    #                         'street2': rec.street2 if rec.street2 else None,
    #                         'city': rec.city if rec.city else None,
    #                         'state_id': rec.state_id.id if rec.state_id else None,
    #                         'zip': rec.zip if rec.zip else None,
    #                         'country_id': rec.country_id.id if rec.country_id else None,
    #                         'phone': rec.phone if rec.phone else None,
    #                         'mobile': rec.mobile if rec.mobile else None,
    #                         'email': rec.email if rec.email else None,
    #                         'user_id': rec.user_id.id if rec.user_id else None,
    #                     }
    #                     customer_list.append(dic)
    #                 return Response(
    #                     json.dumps({'data': customer_list}, sort_keys=True,
    #                                indent=4, cls=ObjectEncoder),
    #                     content_type='application/json;charset=utf-8',
    #                     status=200)
    #             else:
    #                 return {'status': 200, 'message': "Undefined invoices", 'success':False ,
    #                         'body': uid}
    #         else:
    #             return {'status': 202, 'message': 'Token Expired'}
    #     except Exception as error:
    #         _logger.error(error)
    #         abort({'error': traceback.format_exc()}, rollback=True, status=400)

    @http.route(['/api/pointofsale/all/customer/filter/sales/person'], auth="none", type='http',
                csrf=False)
    def pos_all_customer_filter(self, token, **kw):
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)

        try:
            if uid:
                salesperson = kw.get('salesperson_id')
                customer = request.env['res.partner'].sudo().search(
                    [('user_id.id', '=', salesperson)])
                customer_list = []

                if customer:
                    for rec in customer:
                        dic = {
                            'id': rec.id if rec.id else None,
                            'name': rec.name if rec.name else None,
                            'street': rec.street if rec.street else None,
                            'street2': rec.street2 if rec.street2 else None,
                            'city': rec.city if rec.city else None,
                            'state_id': rec.state_id.id if rec.state_id else None,
                            'zip': rec.zip if rec.zip else None,
                            'country_id': rec.country_id.id if rec.country_id else None,
                            'phone': rec.phone if rec.phone else None,
                            'mobile': rec.mobile if rec.mobile else None,
                            'email': rec.email if rec.email else None,
                            'user_id': rec.user_id.id if rec.user_id else None,
                            'ref': rec.ref if rec.ref else None,
                        }
                        customer_list.append(dic)

                    return Response(
                        json.dumps({'data': customer_list}, sort_keys=True, indent=4,
                                   cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200
                    )
                else:
                    return Response(
                        json.dumps(
                            {'status': 200, 'message': "No customers found", 'success': False,
                             'body': uid},
                            sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200
                    )
            else:
                return Response(
                    json.dumps({'status': 202, 'message': 'Token Expired'}, sort_keys=True,
                               indent=4, cls=ObjectEncoder),
                    content_type='application/json;charset=utf-8',
                    status=202
                )
        except Exception as error:
            _logger.error("An error occurred: %s", error, exc_info=True)
            abort({'error': traceback.format_exc()}, rollback=True, status=500)

    ########################################### POS TODAYS SALE AMOUNT #######################################

    @http.route(['/api/pointofsale/all/todays/sale/amount'], auth="none", type='http',
                csrf=False)
    def pos_all_todays_sale_amount(self, token, today=None, **kw):
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        today = datetime.now().date()
        date_start = datetime.combine(today, datetime.min.time())
        date_end = datetime.combine(today, datetime.max.time())
        amount = request.env['sale.order'].sudo().search(
            [('date_order', '>=', date_start), ('date_order', '<=', date_end),
             ('state', '=', 'sale')])
        try:
            if uid:
                if amount:
                    total_amount = 0
                    for rec in amount:
                        total_amount += rec.amount_total
                    amount_list = {'total_amount': "{:.3f}".format(total_amount)}
                    return Response(
                        json.dumps({'data': amount_list}, sort_keys=True,
                                   indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)/home/zinfog/odoo16/odoo-16.0/ideal_pos/idea_global_trading/zcpr_landed_product_cost/__init__.py
                else:
                    msg = "Undefined Amount"
                    success = False
                    return {'status': 200, 'message': msg, 'success': success,
                            'body': uid}
            else:
                return {'status': 202, 'message': 'Token Expired'}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ########################################### POS VIEW NEW ORDERS #######################################

    @http.route(['/api/pointofsale/all/view/new/orders'], auth="none", type='http',
                csrf=False)
    def pos_all_view_orders(self, token, today=None, **kw):
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        today = datetime.now().date()
        date_start = datetime.combine(today, datetime.min.time())
        date_end = datetime.combine(today, datetime.max.time())

        order = request.env['sale.order'].sudo().search(
            [('date_order', '>=', date_start), ('date_order', '<=', date_end),
             ('state', '=', 'sale')], limit=5).sorted()
        try:
            if uid:
                if order:
                    order_list = []
                    for rec in order:
                        for res in rec.order_line:
                            dic = {
                                'id': rec.id if rec.id else None,
                                'name': rec.name if rec.name else None,
                                'partner_id': rec.partner_id.id if rec.partner_id else None,
                                'date_order': str(rec.date_order) if rec.date_order else None,
                                'pricelist_id': rec.pricelist_id.id if rec.pricelist_id else None,
                                'team_id': rec.team_id.id if rec.team_id else None,
                                'product_template_id': res.product_template_id.id if res.product_template_id else None,
                                'product_uom_qty': res.product_uom_qty if res.product_uom_qty else None,
                                'price_unit': "{:.3f}".format(
                                    res.price_unit) if res.price_unit else None,
                                'price_subtotal': "{:.3f}".format(
                                    res.price_subtotal) if res.price_subtotal else None,
                            }
                            order_list.append(dic)
                    return Response(
                        json.dumps({'data': order_list}, sort_keys=True,
                                   indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8', status=200)
                else:
                    msg = "Undefined orders"
                    success = False
                    return {'status': 200, 'message': msg, 'success': success,
                            'body': uid}
            else:
                return {'status': 202, 'message': 'Token Expired'}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ########################################### POS NEW ARRIVED PRODUCT #######################################

    @http.route(['/api/pointofsale/all/new/product'], auth="none", type='http',
                csrf=False)
    def pos_all_new_product(self, token, today=None, **kw):
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)

        product = request.env['product.template'].sudo().search(
            [('new_product', '=', True)])
        try:
            if uid:
                if product:
                    product_list = []
                    for rec in product:
                        dic = {
                            'id': rec.id if rec.id else None,
                            'name': rec.name if rec.name else None,
                            'list_price': "{:.3f}".format(
                                rec.list_price) if rec.list_price else None,
                            'categ_id': rec.categ_id.id if rec.categ_id else None,
                            'arabic_name': rec.name_arabic if rec.name_arabic else None,

                        }
                        product_list.append(dic)
                    return Response(
                        json.dumps({'data': product_list}, sort_keys=True,
                                   indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8', status=200)
                else:
                    msg = "Undefined Products"
                    success = False
                    return {'status': 200, 'message': msg, 'success': success,
                            'body': uid}

            else:
                return {'status': 202, 'message': 'Token Expired'}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ####################################### CREATE NEW CUSTOMER #########################################

    # @http.route(['/api/pointofsale/create/new/customer/<string:token>/'],
    #             auth="public", type='json',
    #             methods=['POST'], csrf=False)
    # def create_new_customers(self, token=None, **kw):
    #     check_params({'token': token})
    #     data = json.loads(request.httprequest.data)
    #     env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
    #     uid = env['sfk_rest.token'].check_token(token)
    #     try:
    #         if uid:
    #             if data['name']:
    #                 customer = request.env['res.partner'].sudo().create(
    #                     {'name': data['name'],
    #                      'phone': data['phone'] if data['phone'] else None,
    #                      'email': data['email'] if data['email'] else None,
    #                      'street': data['street'] if data['street'] else None,
    #                      'street2': data['street2'] if data[
    #                          'street2'] else None,
    #                      'city': data['city'] if data['city'] else None,
    #                      'zip': data['zip'] if data['zip'] else None, })
    #                 msg = "New customer created"
    #                 success = True
    #                 return {'status': 200, 'message': msg, 'success': success, 'customer_id':customer.id,
    #                         'body': uid}
    #             else:
    #                 msg = "Customer creation failed"
    #                 success = False
    #                 return {'status': 200, 'message': msg, 'success': success,
    #                         'body': uid}
    #         else:
    #             return {'status': 202, 'message': "Token Not In The System"}
    #     except Exception as error:
    #         _logger.error(error)
    #         abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ####################################### CREATE ORDER FROM POS #########################################

    @http.route(['/api/pointofsale/create/order/<string:token>/'],
                auth="public", type='json',
                methods=['POST'], csrf=False)
    def create_pos_order(self, token=None, **kw):
        check_params({'token': token})
        data = json.loads(request.httprequest.data)
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                partner = request.env['res.partner'].sudo().browse(int(data['partner_id'])).exists()
                # salesperson = request.env['res.users'].sudo().browse(
                #     int(data['salesperson_id'])).exists()
                if partner:
                    order_line = []
                    for rec in data['product_ids']:
                        product = request.env['product.product'].sudo().browse(int(rec['product_id']))
                        if 'django_orderitems_id' in rec:
                            django_orderitems_id = rec['django_orderitems_id']
                        else:
                            django_orderitems_id = None

                        order_line.append((0, 0, {
                            'product_template_id': product.product_tmpl_id.id,
                            'product_uom_qty': int(rec['qty']),
                            # 'price_unit': int(rec['price']),
                            'name': product.name,
                            'qty_available': product.qty_available,
                            'product_id': product.id,
                            'image_url': rec['img'],
                            'django_orderitems_id': django_orderitems_id,
                            'stock_in_hand': rec['stock']
                        }))

                    order = request.env['sale.order'].sudo().create(
                        {'partner_id': partner.id,
                         'state': 'draft',
                         'branch_id': partner.branch_id.id,
                         'order_line': order_line,
                         'origin': data['Django_id'],
                         # 'user_id': salesperson.id if salesperson else None,
                         })
                    msg = "Order created successfully"
                    success = True
                    return {'status': 200, 'message': msg, 'success': success, 'order_id': order.id,
                            'Django_id': data['Django_id'], 'body': uid}
            else:
                return {'status': 202, 'message': "Token Not In The System"}

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ##################ABIN SURESH API STARTING FROM HERE####

    ########################################### POS VIEW ALL ORDERS #######################################

    @http.route(['/api/pointofsale/all/orders'], auth="none", type='http',
                csrf=False)
    def pos_all_orders(self, token, **kwargs):
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                orders = request.env['sale.order'].sudo().search(
                    [('state', 'in', ['draft', 'sale'])])
                order_list = []
                if orders:
                    for rec in orders:
                        for res in rec.order_line:
                            date_ordered = None
                            if rec.date_order:
                                date_ordered = rec.date_order.strftime('%Y-%m-%d')
                            dic = {
                                'id': rec.id if rec.id else None,
                                'name': rec.name if rec.name else None,
                                'partner_id': rec.partner_id.id if rec.partner_id else None,
                                'branch_id': rec.branch_id.id if rec.branch_id else None,
                                'current_balance_customer': "{:.3f}".format(
                                    rec.current_balance_customer) if rec.current_balance_customer else None,
                                'balance_limit': rec.balance_limit if rec.balance_limit else None,
                                'team_id': rec.team_id.id if rec.team_id else None,
                                'origin': rec.origin if rec.origin else None,
                                'django_orderitems_id': res.django_orderitems_id if res.django_orderitems_id else None,
                                'sales_type': rec.sales_type if rec.sales_type else None,
                                'date_order': date_ordered,
                                'pricelist_id': rec.pricelist_id.id if rec.pricelist_id else None,
                                'product_template_id': res.product_template_id.id if res.product_template_id else None,
                                'product_description': res.name if res.name else None,
                                'qty_available': res.qty_available if res.qty_available else None,
                                'product_uom_quantity': res.product_uom_qty if res.product_uom_qty else None,
                                'qty_delivered': res.qty_delivered if res.qty_delivered else None,
                                'qty_invoiced': res.qty_invoiced if res.qty_invoiced else None,
                                'price_unit': "{:.3f}".format(
                                    res.price_unit) if res.price_unit else None,
                                'tax_id': res.tax_id.ids if res.tax_id else None,
                                'price_subtotal': "{:.3f}".format(
                                    res.price_subtotal) if res.price_subtotal else None,
                                'amount_total': "{:.3f}".format(
                                    rec.amount_total) if rec.amount_total else None,
                            }
                            order_list.append(dic)
                    return Response(
                        json.dumps({'data': order_list}, sort_keys=True,
                                   indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "Undefined sale orders"
                    success = False
                    return {'status': 200, 'message': msg, 'success': success,
                            'body': uid}
            else:
                return {'status': 202, 'message': 'Token Expired'}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

            # @http.route(['/api/pointofsale/all/orders'], auth="none", type='http',

    #             csrf=False)
    # def pos_all_orders(self, token, **kwargs):
    #     ensure_db()
    #     env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
    #     uid = env['sfk_rest.token'].check_token(token)
    #     # orders = request.env['sale.order'].sudo().search(
    #     #     [('state', 'in', ['sale', 'draft'])])
    #     try:
    #         if uid:
    #             orders = request.env['sale.order'].sudo().search(
    #                 [('state', 'in', ['draft', 'sale'])])
    #             order_list = []
    #             if orders:
    #                 for rec in orders:
    #                     for res in rec.order_line:
    #                         dic = {
    #                             'id': rec.id if rec.id else None,
    #                             'name': rec.name if rec.name else None,
    #                             'partner_id': rec.partner_id.id if rec.partner_id else None,
    #                             'branch_id': rec.branch_id.id if rec.branch_id else None,
    #                             'current_balance_customer': rec.current_balance_customer if rec.current_balance_customer else None,
    #                             'balance_limit': rec.balance_limit if rec.balance_limit else None,
    #                             'team_id': rec.team_id.id if rec.team_id else None,
    #                             'sales_type': rec.sales_type if rec.sales_type else None,
    #                             'date_order': rec.date_order if rec.date_order else None,
    #                             'pricelist_id': rec.pricelist_id.id if rec.pricelist_id else None,
    #                             'product_template_id': res.product_template_id.id if res.product_template_id else None,
    #                             'product_description': res.name if res.name else None,
    #                             'qty_available': res.qty_available if res.qty_available else None,
    #                             'product_uom_quantity': res.product_uom_qty if res.product_uom_qty else None,
    #                             'qty_delivered': res.qty_delivered if res.qty_delivered else None,
    #                             'qty_invoiced': res.qty_invoiced if res.qty_invoiced else None,
    #                             'price_unit': res.price_unit if res.price_unit else None,
    #                             'tax_id': res.tax_id.ids if res.tax_id else None,
    #                             'price_subtotal': res.price_subtotal if res.price_subtotal else None,
    #                             'amount_total': rec.amount_total if rec.amount_total else None,
    #                         }
    #                         order_list.append(dic)
    #                 return Response(
    #                     json.dumps({'data': order_list}, sort_keys=True,
    #                                indent=4, cls=ObjectEncoder),
    #                     content_type='application/json;charset=utf-8',
    #                     status=200)
    #             else:
    #                 msg = "Undefined sale orders"
    #                 success = False
    #                 return {'status': 200, 'message': msg, 'success': success,
    #                         'body': uid}
    #         else:
    #             return {'status': 202, 'message': 'Token Expired'}
    #     except Exception as error:
    #         _logger.error(error)
    #         abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ######################################## POS ALL CUSTOMERS #####################################

    @http.route(['/api/pointofsale/all/customers/<string:token>/'], auth="none",
                type='http',
                csrf=False)
    def show_customers_aa(self, token, **kwargs):
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                customers = request.env['res.partner'].sudo().search([])
                partner_list = []
                if customers:
                    for rec in customers:
                        if rec.phone:
                            dic = {
                                'id': rec.id,
                                'name': rec.name if rec.name else None,
                                'street': rec.street if rec.street else None,
                                'street2': rec.street2 if rec.street2 else None,
                                'city': rec.city if rec.city else None,
                                'state_id': rec.state_id.id if rec.state_id else None,
                                'country_id': rec.country_id.id if rec.country_id else None,
                                'zip': rec.zip if rec.zip else None,
                                'phone': rec.phone if rec.phone else None,
                                'email': rec.email if rec.email else None,
                                'ref': rec.ref if rec.ref else None,
                                'branch_id': rec.branch_id.id if rec.branch_id else None,
                                'user_id': rec.user_id.id if rec.user_id else None,
                                'customer_credit_limit': "{:.3f}".format(
                                    rec.customer_credit_limit) if rec.customer_credit_limit else None,
                                'customer_days_notification': rec.customer_days_notification if rec.customer_days_notification else None,
                            }
                            partner_list.append(dic)
                    return Response(
                        json.dumps({'data': partner_list},
                                   sort_keys=True,
                                   indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "Undefined sale orders"
                    success = False
                    return {'status': 200, 'message': msg,
                            'success': success,
                            'body': uid}
            else:
                return {'status': 202, 'message': 'Token Expired'}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True,
                  status=400)

    ######################################## POS ALL PRODUCTS #####################################

    @http.route(['/api/ps/all/products'], auth="none", type='http',
                csrf=False)
    def show_all_products(self, token, **kwargs):
        products = request.env['product.template'].sudo().search([])
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                products = request.env['product.product'].sudo().search([])
                product_list = []
                if products:
                    for rec in products:
                        dic = {
                            'id': rec.id if rec.id else None,
                            'name': rec.name if rec.name else None,
                            'list_price': "{:.3f}".format(
                                rec.list_price) if rec.list_price else None,
                            'taxes_id': rec.taxes_id.ids if rec.taxes_id else None,
                            'item_group': rec.item_group.id if rec.item_group else None,
                            'item_sub_group': rec.item_sub_group.id if rec.item_sub_group else None,
                            'categ_id': rec.categ_id.id if rec.categ_id else None,
                            'product_tag_ids': rec.product_tag_ids.ids if rec.product_tag_ids else None,
                            'arabic_name': rec.product_tmpl_id.name_arabic if rec.product_tmpl_id.name_arabic else None,
                        }
                        product_list.append(dic)
                    return Response(
                        json.dumps({'data': product_list}, sort_keys=True,
                                   indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "Undefined sale orders"
                    success = False
                    return {'status': 200, 'message': msg, 'success': success,
                            'body': uid}
            else:
                return {'status': 202, 'message': 'Token Expired'}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ####################################### CREATE CUSTOMER FROM POS #########################################

    @http.route(['/api/pointofsale/create/customer/<string:token>/'],
                auth="public", type='json',
                methods=['POST'], csrf=False)
    def create_ps_customer(self, token=None, **kw):
        check_params({'token': token})
        data = json.loads(request.httprequest.data)
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                if data['name']:
                    country = request.env['res.country'].sudo().search(
                        [('code', '=', 'OM'), ('name', '=', 'Oman')])
                    print(country.name)
                    customer = request.env['res.partner'].sudo().create(
                        {'name': data['name'],
                         'phone': data['phone'] if data['phone'] else None,
                         'email': data['email'] if data['email'] else None,
                         # 'branch_id': data['branch_id'] if data[
                         #     'branch_id'] else None,
                         # 'customer_credit_limit': data[
                         #     'customer_credit_limit'] if data[
                         #     'customer_credit_limit'] else None,
                         # 'customer_days_notification': data[
                         #     'customer_days_notification'] if data[
                         #     'customer_days_notification'] else None,
                         'street': data['street'] if data['street'] else None,
                         'street2': data['street2'] if data['street2'] else None,
                         'city': data['city'] if data['city'] else None,
                         'state_id': data['state_id'] if data['state_id'] else None,
                         'country_id': country.id,
                         'zip': data['zip'] if data['zip'] else None, })
                    # check_customer=customer.fetch_customer_id()
                    # print(check_customer,'checkcustomerrrrrrrrrrrrrrrrrrrrrrr')
                    msg = "Customer created successfully"
                    success = True
                    return {'status': 200, 'message': msg, 'success': success,
                            "customer_id": customer.id,
                            'body': uid}
                else:
                    msg = "Customer creation failed"
                    success = False
                    return {'status': 200, 'message': msg, 'success': success,
                            'body': uid}
            else:
                return {'status': 202, 'message': "Token Not In The System"}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ####################################### CREATE PRODUCT FROM POS #########################################

    @http.route(['/api/pointofsale/create/product/<string:token>/'],
                auth="public", type='json',
                methods=['POST'], csrf=False)
    def create_pos_products(self, token=None, **kw):
        check_params({'token': token})
        data = json.loads(request.httprequest.data)
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                if data['name']:
                    # for rec in data['lines']:
                    product = request.env['product.template'].sudo().create(
                        {'name': data["name"],
                         'list_price': data["list_price"],
                         'detailed_type': 'product'
                         # 'taxes_id': rec["taxes_id"],
                         # 'standard_price': data["standard_price"],
                         # 'item_group': data["item_group"],
                         # 'item_sub_group': data["item_sub_group"],
                         # 'categ_id': data["categ_id"],
                         # 'product_tag_ids': rec["product_tag_ids"],
                         })
                    msg = "Product created successfully"
                    success = True
                    return {'status': 200, 'message': msg, 'success': success,
                            'product_id': product.id,
                            'body': uid}
                else:
                    msg = "Product creation failed"
                    success = False
                    return {'status': 200, 'message': msg, 'success': success,
                            'body': uid}
            else:
                return {'status': 202, 'message': "Token Not In The System"}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    # @http.route(['/api/pointofsale/create/product/<string:token>/'],
    #             auth="public", type='json',
    #             methods=['POST'], csrf=False)
    # def create_pos_products(self, token=None, **kw):
    #     check_params({'token': token})
    #     data = json.loads(request.httprequest.data)
    #     env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
    #     uid = env['sfk_rest.token'].check_token(token)
    #     try:
    #         if uid:
    #             if data['name']:
    #                 # for rec in data['lines']:
    #                 product = request.env['product.template'].sudo().create(
    #                     {'name': data["name"],
    #                      'list_price': data["list_price"],
    #                      'detailed_type': 'product'
    #                      # 'taxes_id': rec["taxes_id"],
    #                      # 'standard_price': data["standard_price"],
    #                      # 'item_group': data["item_group"],
    #                      # 'item_sub_group': data["item_sub_group"],
    #                      # 'categ_id': data["categ_id"],
    #                      # 'product_tag_ids': rec["product_tag_ids"],
    #                      })
    #                 print(product, "cusssssssssss")
    #                 msg = "Product created successfully"
    #                 success = True
    #                 return {'status': 200, 'message': msg, 'success': success, 'product_id': product.id,
    #                         'body': uid}
    #             else:
    #                 msg = "Order creation failed"
    #                 success = False
    #                 return {'status': 200, 'message': msg, 'success': success,
    #                         'body': uid}
    #         else:
    #             return {'status': 202, 'message': "Token Not In The System"}
    #     except Exception as error:
    #         _logger.error(error)
    #         abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ######################################### WALK-IN CUSTOMER CREATE API(pending) ########################################

    @http.route(['/api/create/walkin/customer/<string:token>/'], auth="public", type='json',
                methods=['POST'], csrf=False)
    def create_walkin_customer(self, token=None, **kw):
        check_params({'token': token})
        data = json.loads(request.httprequest.data)
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                customer = request.env['res.partner'].sudo().search(
                    [('id', '=', request.env.ref('zcl_walkin_customer.walkin_customer_data').id)])
                if customer:
                    if data['name']:
                        customer.walkin_customer_ids = [
                            fields.Command.create({'name': data['name'], 'phone': data['phone']})]
                        msg = "Success"
                        success = True
                        return {'status': 200, 'message': msg, 'success': success,
                                'body': uid}
                else:
                    msg = "Walk-in customer creation failed"
                    success = False
                    return {'status': 200, 'message': msg, 'success': success,
                            'body': uid}
            else:
                return {'status': 202, 'message': "Token Not In The System"}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ################################################ API POS DASHBOARD (pending) ###################################

    @http.route(['/api/pointofsale/dashboard/<string:token>/'], auth="none", type='http',
                csrf=False)
    def show_pos_dashboard(self, token, **kwargs):
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                dashboard_list = []
                order_list = []
                product_list = []
                partner_list = []
                today = datetime.now().date()
                date_start = datetime.combine(today, datetime.min.time())
                date_end = datetime.combine(today, datetime.max.time())
                customers = request.env['res.partner'].sudo().search([])
                products = request.env['product.template'].sudo().search([])
                orders = request.env['sale.order'].sudo().search(
                    [('state', '=', 'sale')])
                today_order_count = request.env[
                    'sale.order'].sudo().search_count(
                    [('state', '=', 'sale'), ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                credit_invoice_count = request.env[
                    'account.move'].sudo().search(
                    [('payment_state', '=', 'not_paid')])
                credit_sale_count = request.env['sale.order'].sudo().search_count(
                    [('invoice_ids', '=', credit_invoice_count.ids), ('state', '=', 'sale')])
                new_product = request.env['product.template'].sudo().search(
                    [('new_product', '=', True)])
                new_orders = request.env['sale.order'].sudo().search(
                    [('date_order', '>=', date_start),
                     ('date_order', '<=', date_end), ('state', '=', ['sale', 'draft'])],
                    limit=5).sorted()
                today_sale_amount = request.env['sale.order'].sudo().search(
                    [('date_order', '>=', date_start),
                     ('date_order', '<=', date_end), ('state', '=', 'sale')])
                cash_payment = request.env['account.payment'].sudo().search(
                    [('journal_id.type', '=', 'cash')])
                for cash in cash_payment:
                    cash_invoice_count = request.env['account.move'].sudo().search(
                        [('name', '=', cash.ref)])
                    if cash_invoice_count:
                        cash_sale_order = request.env['sale.order'].sudo().search_count([('invoice_ids', '=', cash_invoice_count.ids)])
                        if cash_sale_order:
                            dic = {"cash_sale_order": cash_sale_order}
                            dashboard_list.append(dic)
                bank_payment = request.env['account.payment'].sudo().search([('journal_id.type', '=', 'bank')])
                if bank_payment:
                    for bank in bank_payment:
                        bank_invoice_count = request.env['account.move'].sudo().search([('name', '=', bank.ref)])
                        if bank_invoice_count:
                            bank_sale_order = request.env['sale.order'].sudo().search_count([('invoice_ids', '=', bank_invoice_count.ids)])
                            if bank_sale_order:
                                dic = {"bank_sale_order": bank_sale_order}
                                dashboard_list.append(dic)
                if orders:
                    for order in orders:
                        for res in order.order_line:
                            dic = {"all_orders": {
                                'order_id': order.id if order.id else None,
                                'order': order.name if order.name else None,
                                'date_order': str(
                                    order.date_order) if order.date_order else None,
                                'order_partner_id': order.partner_id.id if order.partner_id else None,
                                "team_id": order.team_id.id if order.team_id else None,
                                'amount_total': "{:.3f}".format(order.amount_total) if order.amount_total else None,
                                'product_template_id': res.product_template_id.id if res.product_template_id else None,
                                'qty_available': res.qty_available if res.qty_available else None,
                                'product_uom_quantity': res.product_uom_qty if res.product_uom_qty else None,
                                'qty_delivered': res.qty_delivered if res.qty_delivered else None,
                                'qty_invoiced': res.qty_invoiced if res.qty_invoiced else None,
                                'price_unit': "{:.3f}".format(res.price_unit) if res.price_unit else None,
                                'price_subtotal': "{:.3f}".format(res.price_subtotal) if res.price_subtotal else None,
                            }}
                            order_list.append(dic)
                if products:
                    for product in products:
                        dic = {"all_products": {
                            "product": product.name if product.name else None,
                            "product_id": product.id if product.id else None,
                            'list_price': "{:.3f}".format(product.list_price) if product.list_price else None,
                            'categ_id': product.categ_id.id if product.categ_id else None,
                        }}
                        product_list.append(dic)
                if customers:
                    for customer in customers:
                        dic = {"all_customers": {
                            'customer_id': customer.id if customer.id else None,
                            'customer': customer.name if customer.name else None,
                            'street': customer.street if customer.street else None,
                            'street2': customer.street2 if customer.street2 else None,
                            'city': customer.city if customer.city else None,
                            'state_id': customer.state_id.id if customer.state_id else None,
                            'country_id': customer.country_id.id if customer.country_id else None,
                            'zip': customer.zip if customer.zip else None,
                            'phone': customer.phone if customer.phone else None,
                            'mobile': customer.mobile if customer.mobile else None,
                            'email': customer.email if customer.email else None,
                        }}
                        partner_list.append(dic)
                if today_order_count:
                    dic = {"today_sales_count": today_order_count}
                    dashboard_list.append(dic)
                if credit_sale_count:
                    dic = {"credit_sale_count": credit_sale_count}
                    dashboard_list.append(dic)
                if new_product:
                    for rec in new_product:
                        dic = {"new_products": {
                            'id': rec.id if rec.id else None,
                            'name': rec.name if rec.name else None,
                            'list_price': "{:.3f}".format(rec.list_price) if rec.list_price else None,
                            'categ_id': rec.categ_id.id if rec.categ_id else None,
                        }}
                        dashboard_list.append(dic)
                if new_orders:
                    for rec in new_orders:
                        for res in rec.order_line:
                            dic = {"new_orders": {
                                'id': rec.id if rec.id else None,
                                'name': rec.name if rec.name else None,
                                'partner_id': rec.partner_id.id if rec.partner_id else None,
                                'date_order': str(rec.date_order) if rec.date_order else None,
                                'pricelist_id': rec.pricelist_id.id if rec.pricelist_id else None,
                                'team_id': rec.team_id.id if rec.team_id else None,
                                'product_template_id': res.product_template_id.id if res.product_template_id else None,
                                'product_uom_qty': res.product_uom_qty if res.product_uom_qty else None,
                                'price_unit': "{:.3f}".format(res.price_unit) if res.price_unit else None,
                                'price_subtotal': "{:.3f}".format(res.price_subtotal) if res.price_subtotal else None,
                            }}
                            dashboard_list.append(dic)
                if today_sale_amount:
                    total_amount = 0
                    for rec in today_sale_amount:
                        total_amount += rec.amount_total
                    amount_list = {'total_sales_amount': "{:.3f}".format(total_amount)}
                    dashboard_list.append(amount_list)
                dashboard_list.append(partner_list)
                dashboard_list.append(product_list)
                dashboard_list.append(order_list)
                sale_order_ids = request.env['sale.order'].sudo().search([('state', 'in', ['sale', 'done'])])
                cust_list = []
                top_list = []
                if sale_order_ids:
                    customer_list = []
                    customer_data = []
                    for order in sale_order_ids:
                        total_amount = 0
                        if order.partner_id not in customer_list:
                            customer_list.append(order.partner_id)
                            for customer in sale_order_ids:
                                if order.partner_id == customer.partner_id:
                                    total_amount += customer.amount_total
                            customer_dict = {'customers': order.partner_id.id, 'amount': total_amount}
                            customer_data.append(customer_dict)
                    sorted_customer_data = sorted(customer_data, key=lambda x: x['amount'], reverse=True)
                    for customer_dict in sorted_customer_data[:5]:
                        cust_list.append(customer_dict.get('customers'))
                    if cust_list:
                        top_cus = request.env['res.partner'].sudo().search([('id', 'in', cust_list)])
                        for top in top_cus:
                            dic = {"top_customer": {
                                'customer_id': top.id if top.id else None,
                                'customer': top.name if top.name else None,
                                'phone': top.phone if top.phone else None,
                            }}
                            top_list.append(dic)
                dashboard_list.append(top_list)
                return Response(
                    json.dumps({'data': dashboard_list}, sort_keys=True,
                               indent=4, cls=ObjectEncoder),
                    content_type='application/json;charset=utf-8',
                    status=200)
            else:
                return {'status': 202, 'message': "Token Not In The System"}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

            # @http.route(['/api/pointofsale/dashboard/<string:token>/'], auth="none",

    #             type='http', csrf=False)
    # def show_pos_dashboard(self, token, **kwargs):
    #     ensure_db()
    #     env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
    #     uid = env['sfk_rest.token'].check_token(token)
    #     try:
    #         if uid:
    #             dashboard_list = []
    #             order_list = []
    #             product_list = []
    #             partner_list = []
    #             today = datetime.now().date()
    #             date_start = datetime.combine(today, datetime.min.time())
    #             date_end = datetime.combine(today, datetime.max.time())
    #             customers = request.env['res.partner'].sudo().search([])
    #             products = request.env['product.template'].sudo().search([])
    #             orders = request.env['sale.order'].sudo().search(
    #                 [('state', '=', 'sale')])
    #             today_order_count = request.env[
    #                 'sale.order'].sudo().search_count(
    #                 [('state', '=', 'sale'), ('date_order', '>=', date_start),
    #                  ('date_order', '<=', date_end)])
    #             credit_invoice_count = request.env[
    #                 'account.move'].sudo().search(
    #                 [('payment_state', '=', 'not_paid')])
    #             print(credit_invoice_count, "credit_invoice_count")
    #             credit_sale_count = request.env[
    #                 'sale.order'].sudo().search_count(
    #                 [('invoice_ids', '=', credit_invoice_count.ids)])
    #             new_product = request.env['product.template'].sudo().search(
    #                 [('new_product', '=', True)])
    #             new_orders = request.env['sale.order'].sudo().search(
    #                 [('date_order', '>=', date_start),
    #                  ('date_order', '<=', date_end), ('state', '=', 'sale')],
    #                 limit=5).sorted()
    #             today_sale_amount = request.env['sale.order'].sudo().search(
    #                 [('date_order', '>=', date_start),
    #                  ('date_order', '<=', date_end), ('state', '=', 'sale')])
    #             cash_payment = request.env['account.payment'].sudo().search(
    #                 [('journal_id.type', '=', 'cash')])
    #             print(cash_payment, "cash_paymenttttttttttttt")
    #             bank_payment = request.env['account.payment'].sudo().search(
    #                 [('journal_id.type', '=', 'bank')])
    #             print(bank_payment, "bank_paymenttttttt")
    #             # if cash_payment:
    #             #     cash_invoice_count = request.env[
    #             #         'account.move'].sudo().search(
    #             #         [('payment_id', '=', cash_payment.id)])
    #             #     cash_sale_order = request.env['sale.order'].sudo().search(
    #             #         [('invoice_ids', '=', cash_invoice_count.id)])
    #             #     print(cash_invoice_count,
    #             #           "cash_invoice_count,,,,,,,,,,,,,,,")
    #             #     print(cash_sale_order, "cash_sale_order")
    #             if bank_payment:
    #                 bank_invoice_count = request.env[
    #                     'account.move'].sudo().search(
    #                     [('payment_id', '=', bank_payment.id)])
    #                 print(bank_invoice_count,
    #                       "bank_invoice_count*******")
    #                 bank_sale_order = request.env['sale.order'].sudo().search(
    #                     [('invoice_ids', '=', bank_invoice_count.ids)])
    #                 print(bank_sale_order, "bank_sale_order")
    #             if orders:
    #                 for order in orders:
    #                     for res in order.order_line:
    #                         dic = {"all_orders": {
    #                             'order_id': order.id if order.id else None,
    #                             'order': order.name if order.name else None,
    #                             'date_order': str(
    #                                 order.date_order) if order.date_order else None,
    #                             'order_partner_id': order.partner_id.id if order.partner_id else None,
    #                             "team_id": order.team_id.id if order.team_id else None,
    #                             'amount_total': order.amount_total if order.amount_total else None,
    #                             'product_template_id': res.product_template_id.id if res.product_template_id else None,
    #                             'qty_available': res.qty_available if res.qty_available else None,
    #                             'product_uom_quantity': res.product_uom_qty if res.product_uom_qty else None,
    #                             'qty_delivered': res.qty_delivered if res.qty_delivered else None,
    #                             'qty_invoiced': res.qty_invoiced if res.qty_invoiced else None,
    #                             'price_unit': res.price_unit if res.price_unit else None,
    #                             'price_subtotal': res.price_subtotal if res.price_subtotal else None,
    #                         }}
    #                         order_list.append(dic)
    #             if products:
    #                 for product in products:
    #                     dic = {"all_products": {
    #                         "product": product.name if product.name else None,
    #                         "product_id": product.id if product.id else None,
    #                         'list_price': product.list_price if product.list_price else None,
    #                         'categ_id': product.categ_id.id if product.categ_id else None,
    #                     }}
    #                     product_list.append(dic)
    #             if customers:
    #                 for customer in customers:
    #                     dic = {"all_customers": {
    #                         'customer_id': customer.id if customer.id else None,
    #                         'customer': customer.name if customer.name else None,
    #                         'street': customer.street if customer.street else None,
    #                         'street2': customer.street2 if customer.street2 else None,
    #                         'city': customer.city if customer.city else None,
    #                         'state_id': customer.state_id.id if customer.state_id else None,
    #                         'country_id': customer.country_id.id if customer.country_id else None,
    #                         'zip': customer.zip if customer.zip else None,
    #                         'phone': customer.phone if customer.phone else None,
    #                         'email': customer.email if customer.email else None,
    #                     }}
    #                     partner_list.append(dic)
    #             if today_order_count:
    #                 dic = {"today_sales_count": today_order_count}
    #                 dashboard_list.append(dic)
    #             if credit_sale_count:
    #                 dic = {"credit_sale_count": credit_sale_count}
    #                 dashboard_list.append(dic)
    #             if new_product:
    #                 for rec in new_product:
    #                     dic = {"new_products": {
    #                         'id': rec.id if rec.id else None,
    #                         'name': rec.name if rec.name else None,
    #                         'list_price': rec.list_price if rec.list_price else None,
    #                         'categ_id': rec.categ_id.id if rec.categ_id else None,
    #                     }}
    #                     dashboard_list.append(dic)
    #             if new_orders:
    #                 for rec in new_orders:
    #                     for res in rec.order_line:
    #                         dic = {"new_orders": {
    #                             'id': rec.id if rec.id else None,
    #                             'name': rec.name if rec.name else None,
    #                             'partner_id': rec.partner_id.id if rec.partner_id else None,
    #                             'date_order': str(
    #                                 rec.date_order) if rec.date_order else None,
    #                             'pricelist_id': rec.pricelist_id.id if rec.pricelist_id else None,
    #                             'team_id': rec.team_id.id if rec.team_id else None,
    #                             'product_template_id': res.product_template_id.id if res.product_template_id else None,
    #                             'product_uom_qty': res.product_uom_qty if res.product_uom_qty else None,
    #                             'price_unit': res.price_unit if res.price_unit else None,
    #                             'price_subtotal': res.price_subtotal if res.price_subtotal else None,
    #                         }}
    #                         dashboard_list.append(dic)
    #                 for customer in new_orders.partner_id:
    #                     dic = {"top_customers": {
    #                         'customer_id': customer.id if customer.id else None,
    #                         'customer': customer.name if customer.name else None,
    #                         'street': customer.street if customer.street else None,
    #                         'street2': customer.street2 if customer.street2 else None,
    #                         'city': customer.city if customer.city else None,
    #                         'state_id': customer.state_id.id if customer.state_id else None,
    #                         'country_id': customer.country_id.id if customer.country_id else None,
    #                         'zip': customer.zip if customer.zip else None,
    #                         'phone': customer.phone if customer.phone else None,
    #                         'email': customer.email if customer.email else None,
    #                     }}
    #                     dashboard_list.append(dic)
    #             if today_sale_amount:
    #                 total_amount = 0
    #                 for rec in today_sale_amount:
    #                     total_amount += rec.amount_total
    #                 amount_list = {'total_sales_amount': total_amount}
    #                 dashboard_list.append(amount_list)
    #             dashboard_list.append(partner_list)
    #             dashboard_list.append(product_list)
    #             dashboard_list.append(order_list)
    #             return Response(
    #                 json.dumps({'data': dashboard_list}, sort_keys=True,
    #                            indent=4, cls=ObjectEncoder),
    #                 content_type='application/json;charset=utf-8',
    #                 status=200)
    #         else:
    #             return {'status': 202, 'message': "Token Not In The System"}
    #     except Exception as error:
    #         _logger.error(error)
    #         abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ##################ABDUL HAKEEM API STARTING FROM HERE######

    ##############################New POS ProductLIst#############################

    @http.route(['/api/point/of/sale/product/list'], auth="public", type='http', csrf=False)
    def point_of_sale_product_list(self, token=None, **kw):
        product_list_pos = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)

        try:
            if uid:
                point_of_sale_products = request.env['product.product'].sudo().search([('active', '=', True)])
                if point_of_sale_products:
                    for product in point_of_sale_products:
                        pos_qty = request.env['stock.quant'].sudo().search([('product_id.id', '=', product.id), ('quantity', '>', 0)])
                        if product.product_code and product.list_price:
                            if product.categ_id:

                                # Check if there are any stock quantities for the product
                                if pos_qty:
                                    rec = pos_qty[0]  # Assuming there's only one record for a product
                                    dic = {
                                        'id': product.id if id else None,
                                        'name': product.name if product.name else None,
                                        'arabic_name': product.name_arabic if product.name_arabic else None,
                                        'product_code': product.product_code if product.product_code else None,
                                        'product_category': product.categ_id.id if product.categ_id else None,
                                        'description': product.description_sale if product.description_sale else None,
                                        'product_price': "{:.3f}".format(product.list_price) if product.list_price else None,
                                        'onhand_qty': rec.quantity if rec.quantity else None,
                                        'item_group': product.item_group.id if product.item_group else None,
                                        'item_sub_group': product.item_sub_group.id if product.item_sub_group else None,
                                        'box': product.box if product.box else None,
                                        'bag': product.bag if product.bag else None,
                                        'stock_in_hand': max(rec.available_quantity, 0) if rec.available_quantity else 0,
                                        'image': product.image_1920.decode("utf-8") if product.image_1920 else None,
                                    }
                                    product_list_pos.append(dic)
                    msg = "Success"
                    success = True
                    return Response(json.dumps({"data": product_list_pos, 'message': msg, 'success': success},
                                               sort_keys=True, indent=4, cls=ObjectEncoder),
                                    content_type='application/json;charset=utf-8', status=200)
            else:
                msg = "Token authentication failed"
                success = False
                result = None
                return Response(json.dumps({"data": result, 'message': msg, 'success': success},
                                           sort_keys=True, indent=4, cls=ObjectEncoder),
                                content_type='application/json;charset=utf-8', status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ###############################POS  Return List#############################
    # @http.route(['/api/point/sale/return/list'], auth="public", methods=['GET'], type='http', csrf=False)
    # def point_of_sale_return(self, token, **kwargs):
    #     sale_list_pos = []
    #     check_params({'token': token})
    #     ensure_db()
    #     env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
    #     uid = env['sfk_rest.token'].check_token(token)
    #     try:
    #         if uid:
    #             point_of_sale_return = request.env['sale.order'].sudo().search([('state', '=', 'return')])
    #             if point_of_sale_return:
    #                 for sale in point_of_sale_return:
    #                     sale_order_lines = sale.order_line
    #
    #                     sale_lines = []
    #
    #                     for order_line in sale_order_lines:
    #                         line_data = {
    #                             'product_id': order_line.product_id.name,
    #                             'product_uom_qty': order_line.product_uom_qty if order_line.product_uom_qty else None,
    #                             'price_unit': order_line.price_unit if order_line.price_unit else None,
    #                         }
    #                         sale_lines.append(line_data)
    #
    #                     dic = {
    #                         'id': sale.id if sale.id else None,
    #                         'name': sale.name if sale.name else None,
    #                         'amount_total': sale.amount_total if sale.amount_total else None,
    #                         'create_date': sale.create_date.date().isoformat() if sale.create_date else None,
    #                         'order_lines': sale_lines
    #
    #                     }
    #                     sale_list_pos.append(dic)
    #                 msg = "Success"
    #                 success = True
    #                 return Response(json.dumps({"data": sale_list_pos, 'message': msg, 'success': success},
    #                                            sort_keys=True, indent=4, cls=ObjectEncoder),
    #                                 content_type='application/json;charset=utf-8', status=200)
    #         else:
    #             msg = "Token authentication failed"
    #             success = False
    #             result = None
    #             return Response(json.dumps({"data": result, 'message': msg, 'success': success},
    #                                        sort_keys=True, indent=4, cls=ObjectEncoder),
    #                             content_type='application/json;charset=utf-8', status=202)
    #     except Exception as error:
    #         _logger.error(error)
    #         abort({'error': traceback.format_exc()}, rollback=True, status=400)

    @http.route(['/api/point/sale/return/list'], auth="public", methods=['GET'], type='http', csrf=False)
    def point_of_sale_return(self, token, **kwargs):
        sale_list_pos = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                point_of_sale_return = request.env['sale.order'].sudo().search([('state', '=', 'return')])
                if point_of_sale_return:
                    for sale in point_of_sale_return:
                        sale_order_lines = sale.order_line
                        sale_lines = []
                        for order_line in sale_order_lines:
                            line_data = {
                                'product_id': order_line.product_id.id,
                                'product_uom_qty': order_line.product_uom_qty if order_line.product_uom_qty else None,
                                'price_unit': "{:.3f}".format(order_line.price_unit) if order_line.price_unit else None,
                            }
                            sale_lines.append(line_data)
                        dic = {
                            'id': sale.id if sale.id else None,
                            'name': sale.name if sale.name else None,
                            'amount_total': "{:.3f}".format(sale.amount_total) if sale.amount_total else None,
                            'create_date': sale.create_date.date().isoformat() if sale.create_date else None,
                            'order_lines': sale_lines
                        }
                        sale_list_pos.append(dic)
                    msg = "Success"
                    success = True
                    return Response(json.dumps({"data": sale_list_pos, 'message': msg, 'success': success},
                                               sort_keys=True, indent=4, cls=ObjectEncoder),
                                    content_type='application/json;charset=utf-8', status=200)
                else:
                    msg = "There is no sale return in the database"
                    success = False
                    result = None
                    return Response(json.dumps({"data": result, 'message': msg, 'success': success},
                                               sort_keys=True, indent=4, cls=ObjectEncoder),
                                    content_type='application/json;charset=utf-8', status=202)
            else:
                msg = "Token authentication failed"
                success = False
                result = None
                return Response(json.dumps({"data": result, 'message': msg, 'success': success},
                                           sort_keys=True, indent=4, cls=ObjectEncoder),
                                content_type='application/json;charset=utf-8', status=202)
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

            ############################## POS Create Returns(Pending get method)  ##############################

    @http.route(['/api/point/create/return/list'], auth="public", methods=['GET'], type='http', csrf=False)
    def create_sale_return_pos(self, token, **kwargs):
        create_list_pos = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                create_sale_return = request.env['sale.order'].sudo().search([('state', '=', 'return')])
                if create_sale_return:
                    for sale in create_sale_return:
                        sale_order_lines = sale.order_line
                        sale_lines = []
                        for order_line in sale_order_lines:
                            line_data = {
                                'product_id': order_line.product_template_id.name,
                                'product_uom_qty': order_line.product_uom_qty if order_line.product_uom_qty else None,
                                'price_unit': order_line.price_unit if order_line.price_unit else None,
                            }
                            sale_lines.append(line_data)

                        dict = {
                            'id': sale.id if sale.id else None,
                            'name': sale.name if sale.name else None,
                            'amount_total': sale.amount_total if sale.amount_total else None,
                            'create_date': sale.create_date.date().isoformat() if sale.create_date else None,
                            'line_ids': sale.id,
                            'order_lines': sale_lines,
                        }
                        create_list_pos.append(dict)
                        msg = "Success"
                        success = True
                        return Response(json.dumps({"data": create_list_pos, 'message': msg, 'success': success},
                                                   sort_keys=True, indent=4, cls=ObjectEncoder),
                                        content_type='application/json;charset=utf-8', status=200)
            else:
                msg = "Token authentication failed"
                success = False
                result = None
                return Response(json.dumps({"data": result, 'message': msg, 'success': success},
                                           sort_keys=True, indent=4, cls=ObjectEncoder),
                                content_type='application/json;charset=utf-8', status=202)
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    #############################POS Return Request###################################################
    @http.route(['/api/point/return/request/<string:token>/'], auth="public", methods=['POST'],
                type='json', csrf=False)
    def return_request_pos(self, token, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            if uid:
                partner = request.env['res.partner'].browse(int(data['partner_id'])).exists()
                if partner:
                    order_line = []
                    for rec in data['product_ids']:
                        product = request.env['product.product'].browse(int(rec['product_id']))

                        tax_rate = 5.0
                        tax_id = self.get_or_create_tax(tax_rate)

                        order_line.append((0, 0, {
                            'product_template_id': product.id,
                            'product_uom_qty': int(rec.get('qty', 0)),
                            'name': product.name,
                            'qty_available': product.qty_available,
                            'product_id': product.id,
                            'tax_id': [(6, 0, [tax_id])] if tax_id else False,
                            'price_unit': int(rec.get('price', 0)),
                            'discount_on_foc': int(rec.get('foc', 0)),
                            'image_url': rec.get('img', ''),
                            'stock_in_hand': rec.get('stock', ''),
                        }))
                    order = request.env['sale.order'].sudo().create({
                        'partner_id': partner.id,
                        'state': 'draft',
                        'sale_return': True,
                        "branch_id":partner.branch_id.id if partner.branch_id else None,
                        'order_line': order_line,
                    })
                    msg = "Sale Return Request Successfully"
                    success = True

                    return {'status': 200, 'message': msg, 'success': success, 'body': uid, 'order_id': order.id}
                else:
                    return {'status': 202, 'message': "Token Not In The System"}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    def get_or_create_tax(self, rate):
        tax = request.env['account.tax'].sudo().search([('amount', '=', rate), ('type_tax_use', '=', 'sale')], limit=1)
        if not tax:
            tax = request.env['account.tax'].sudo().create({
                'name': f"{rate}% Tax",
                'amount': rate,
                'type_tax_use': 'sale',
            })
        return tax.id
############################# Request Return Wizards ##########################
    # @http.route(['/api/point/request/return/wizards'], auth="public", methods=['POST'], type='json', csrf=False)
    # def return_request_wizards_pos(self, token=None, **kwargs):
    #     print("oooooooooooooooooooooo")
    #     try:
    #         data = json.loads(request.httprequest.data)
    #         env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
    #         uid = env['sfk_rest.token'].check_token(data['token'])
    #         wizard_data = []
    #
    #         if uid:
    #
    #             sale_order_lines = request.env['sale.order.line'].search(
    #                 [('id', '=', data['partner_id'])])
    #
    #             wizard_lines = request.env['sale.order.line'].search(
    #                 [('id', '!=', data['line_id']),
    #                  ('product_id', '=', sale_order_lines.product_id.id),
    #                  ('product_uom_qty', '>=', sale_order_lines.product_uom_qty),
    #                  ('sale_return', '=', False), ('return_sale', '=', False)])
    #             print("RRRRRRRRRRRRRRRRRRRRRRR")
    #
    #             for rec in wizard_lines:
    #                 print("yyyyyyyyyyyyyyyyy")
    #                 component = {
    #                     'invoice_number': rec.order_id.invoice_ids[0].name if rec.order_id.invoice_ids and
    #                                                                           rec.order_id.invoice_ids[
    #                                                                               0].name else None,
    #                     'sale_order': rec.order_id.id,
    #                     'sale_order_line': rec.id,
    #                     'product_id': rec.product_id.id,
    #                     'name': rec.product_id.name,
    #                     'qty': rec.product_uom_qty,
    #                     'tax_id': rec.tax_id.ids,
    #                     'price_unit': rec.price_unit,
    #                     'sub_total': rec.price_subtotal,
    #                 }
    #                 print("component", component)
    #                 wizard_data.append(component)
    #                 msg = " Return Request Successfully"
    #                 success = True
    #
    #                 return {'status': 200, 'message': msg, 'success': success, 'body': uid, 'wizard_data': wizard_data}
    #             else:
    #                 return {'status': 202, 'message': "Token Not In The System"}
    #     except Exception as error:
    #         _logger.error(error)
    #         abort({'error': traceback.format_exc()}, rollback=True, status=400)
    #

#######################################

    @http.route(['/api/point/request/return/wizards'], auth="public", methods=['POST'], type='json', csrf=False)
    def return_request_wizards_pos(self, token=None, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(data['token'])
            wizard_data = []

            if uid:
                partner_id = data.get('partner_id')
                product_id = data.get('product_id')
                qty = data.get('qty')

                sale_order_lines = request.env['sale.order.line'].sudo().search([
                    ('order_id.partner_id.id', '=', partner_id),
                    ('product_id', '=', product_id),
                    ('product_uom_qty', '>=', qty),
                    ('order_id.sale_return', '=', False),
                    ('state', '=', 'sale')
                ])
                for rec in sale_order_lines:
                    if rec.order_id.invoice_ids:
                        component = {
                            'invoice_number': rec.order_id.invoice_ids[0].name if rec.order_id.invoice_ids and
                                                                                  rec.order_id.invoice_ids[
                                                                                      0].name else None,
                            'sale_order': rec.order_id.id,
                            'sale_order_line': rec.id,
                            'product_id': rec.product_id.id,
                            'name': rec.product_id.name,
                            'qty': rec.product_uom_qty,
                            'tax_id': rec.tax_id.ids,
                            'django_orderitems_id': rec.django_orderitems_id if rec.django_orderitems_id else None,
                            'price_unit': "{:.3f}".format(rec.price_unit),
                            'sub_total': "{:.3f}".format(rec.price_subtotal),
                            'django_id': rec.order_id.origin if rec.order_id.origin else None
                        }
                        wizard_data.append(component)
                msg = "Return Request Successfully"
                success = True
                return {'status': 200, 'message': msg, 'success': success, 'body': uid, 'wizard_data': wizard_data,
                        }
            else:
                return {'status': 202, 'message': "Token Not In The System"}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)


    #############################POS Return Request###################################################

    # @http.route(['/api/point/return/request/'], auth="public", methods=['POST'], type='json', csrf=False)
    # def return_request_pos(self, token=None, **kwargs):
    #     print("oooooooooooooooooooooo")
    #     try:
    #         data = json.loads(request.httprequest.data)
    #         env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
    #         uid = env['sfk_rest.token'].check_token(data['token'])
    #         line_id = []
    #
    #         if uid:
    #             partner = request.env['res.partner'].browse(int(data['partner_id'])).exists()
    #             print("pppppppppppppppppppppppppppp")
    #
    #             if partner:
    #                 order_line = []
    #
    #                 for rec in data['product_ids']:
    #                     product = request.env['product.product'].browse(int(rec['product_id']))
    #
    #                     tax_rate = 5.0
    #                     tax_id = self.get_or_create_tax(tax_rate)
    #
    #                     order_line.append((0, 0, {
    #                         'product_template_id': product.id,
    #                         'product_uom_qty': int(rec.get('qty', 0)),
    #                         'name': product.name,
    #                         'qty_available': product.qty_available,
    #                         'product_id': product.id,
    #                         'tax_id': [(6, 0, [tax_id])] if tax_id else False,
    #                         'price_unit': int(rec.get('price', 0)),
    #                         'discount_on_foc': int(rec.get('foc', 0)),
    #                         'image_url': rec.get('img', ''),
    #                         'stock_in_hand': rec.get('stock', ''),
    #                     }))
    #                     print("eeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
    #
    #                 order = request.env['sale.order'].sudo().create({
    #                     'partner_id': partner.id,
    #                     'state': 'draft',
    #                     'sale_return': True,
    #                     'order_line': order_line,
    #                 })
    #                 print("order", order, "hhhhhhhhhhhhhhhhhhh")
    #
    #                 for rec in order.order_line:
    #                     line_id.append(rec.id)
    #
    #                 msg = "Sale Return Request Successfully"
    #                 success = True
    #
    #                 return {'status': 200, 'message': msg, 'success': success, 'body': uid, 'order_id': order.id,
    #                         'lines_id': line_id}
    #             else:
    #                 return {'status': 202, 'message': "Token Not In The System"}
    #     except Exception as error:
    #         _logger.error(error)
    #         abort({'error': traceback.format_exc()}, rollback=True, status=400)
    #
    # def get_or_create_tax(self, rate):
    #     tax = request.env['account.tax'].sudo().search([('amount', '=', rate), ('type_tax_use', '=', 'sale')], limit=1)
    #     if not tax:
    #         tax = request.env['account.tax'].sudo().create({
    #             'name': f"{rate}% Tax",
    #             'amount': rate,
    #             'type_tax_use': 'sale',
    #         })
    #     return tax.id
    #
    #

    # @http.route(['/api/point/return/request/<string:token>/'], auth="public", methods=['POST'], type='json', csrf=False)
    # def return_request_pos(self, token, **kwargs):
    #     try:
    #         data = json.loads(request.httprequest.data)
    #         env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
    #         uid = env['sfk_rest.token'].check_token(token)
    #         if uid:
    #             partner = request.env['res.partner'].browse(int(data['partner_id'])).exists()
    #             if partner:
    #                 order_line = []
    #                 for rec in data['product_ids']:
    #                     product = request.env['product.product'].browse(int(rec['product_id']))
    #                     order_line.append((0, 0, {
    #                         'product_template_id': product.id,
    #                         'product_uom_qty': int(rec['qty']),
    #                         'name': product.name,
    #                         'qty_available': product.qty_available,
    #                         'product_id': product.id,
    #                         # 'price_unit': int(rec['price']),
    #                         'discount_on_foc': int(rec['foc']),
    #                         'image_url': rec['img'],
    #                         'stock_in_hand': rec['stock']
    #                     }))
    #                 order = request.env['sale.order'].sudo().create({
    #                     'partner_id': partner.id,
    #                     'state': 'draft',
    #                     'sale_return': True,
    #                     'order_line': order_line,
    #                 })
    #                 msg = "Sale Return Request Successfully"
    #                 success = True
    #                 return {'status': 200, 'message': msg, 'success': success, 'body': uid, 'order_id': order.id}
    #             else:
    #                 return {'status': 202, 'message': "Token Not In The System"}
    #
    #         # if uid:
    #         #     return_request_sale = request.env['sale.order'].sudo().search([('state', '=', 'sale'), ('partner_id', '=', int(data['partner_id']))])
    #         #
    #         #     if return_request_sale:
    #         #
    #         #         sale_return = request.env['sale.order'].sudo().create({
    #         #             'partner_id': int(data['partner_id']),
    #         #
    #         #             'state': 'return',
    #         #
    #         #         })
    #         #         msg = "Sale Return  Created Sucessfully"
    #         #         success = True
    #         #         return {'status': 200, 'message': msg, 'success': success, 'return_id': sale_return.id,
    #         #                 'body': uid}
    #     except Exception as error:
    #         _logger.error(error)
    #         abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ####################### POS Order Details (pending) #####################################

    @http.route(['/api/point/order/details'], auth="public", methods=['GET'], type='http', csrf=False)
    def create_order_details_pos(self, token=None, **kw):
        print("deffffffffffffffffffffffffffffffffffff")
        details_list_pos = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                details_list = request.env['sale.order'].sudo().search([])
                if details_list:
                    for line in details_list.order_line:
                        dic = {
                            'description': line.product_id.description_sale,
                            'product_price': "{:.3f}".format(line.product_id.product_tmpl_id.list_price),
                            # 'line_id': line.id
                        }
                        details_list_pos.append(dic)
                        msg = "Success"
                        success = True
                        return Response(json.dumps({"data": details_list_pos, 'message': msg, 'success': success},
                                                   sort_keys=True, indent=4, cls=ObjectEncoder),
                                        content_type='application/json;charset=utf-8', status=200)
            else:
                msg = "Token authentication failed"
                success = False
                result = None
                return Response(json.dumps({"data": result, 'message': msg, 'success': success},
                                           sort_keys=True, indent=4, cls=ObjectEncoder),
                                content_type='application/json;charset=utf-8', status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    #############

    ##################SAYOOJ API STARTING FROM HERE######

    ################################CREATE CUSTOMER UNDER SALES PERSON ##########################################

    @http.route(['/api/create/customer/under/salesperson/<string:token>/'], auth="public", type='json',
                methods=['POST'], csrf=False)
    def create_customer_under_salesperson(self, token=None, **kw):
        print('defffffffffffffffffffffffff')
        check_params({'token': token})
        data = json.loads(request.httprequest.data)
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                if data['sales_person_id']:
                    country = request.env['res.country'].sudo().search([('code', '=', 'OM'), ('name', '=', 'Oman')])
                    sales_person = request.env['res.users'].sudo().search([('id', '=', int(data['sales_person_id']))])
                    print(sales_person, "wwwwwwwwwwwww")
                    if sales_person:
                        if data['name'] and data['phone']:
                            customer = request.env['res.partner'].sudo().create({
                                'name': data.get('name'),
                                # 'building_name': data.get('building'),
                                'street': data.get('street1'),
                                'street2': data.get('street2'),
                                'city': data.get('city'),
                                'state_id': int(data.get('state_id')),
                                'country_id': country.id,
                                'zip': data.get('zip'),
                                'phone': int(data.get('phone')),
                                'email': data.get('email'),
                                'user_id': sales_person.id,
                                'company_type': 'person',

                            })
                            msg = "success"
                            success = True
                            return {'status': 200, 'message': msg, 'success': success, 'customer_id': customer.id,
                                    'body': uid}
                        else:
                            msg = "Missing required field Name or Phone"
                            success = False
                            return {'status': 200, 'message': msg, 'success': success,
                                    'body': uid}
                    else:
                        msg = "Sale person not found"
                        success = False
                        return {'status': 200, 'message': msg, 'success': success,
                                'body': uid}
            else:
                return {'status': 202, 'message': "Token Not In The System"}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ############################# Merlin ###################################################
    ############################# STATE API ###################################################

    @http.route(['/api/search/state'], auth="public", type='http', csrf=False)
    def search_state(self, token=None, **kw):
        state_list = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                state_details = request.env['res.country.state'].sudo().search([('country_id.code', '=', 'OM')])
                if state_details:
                    for i in state_details:
                        dic = {
                            'id': i.id if i.id else None,
                            'name': i.name if i.name else None
                        }
                        state_list.append(dic)
                    msg = "Success"
                    success = True
                    return Response(json.dumps(
                        {"data": state_list, 'message': msg,
                         'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "Failed"
                    success = False
                    result = None
                    return Response(json.dumps(
                        {"data": result, 'message': msg, 'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)

            msg = "Token authentication failed"
            success = False
            result = None
            return Response(
                json.dumps({"data": result, 'message': msg, 'success': success},
                           sort_keys=True, indent=4, cls=ObjectEncoder),
                content_type='application/json;charset=utf-8', status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

            #####################LIst country################

    @http.route(['/api/search/country'], auth="public", type='http', csrf=False)
    def search_country(self, token=None, **kw):
        country_list = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)

        try:
            if uid:
                country_details = request.env['res.country'].sudo().search(
                    [])

                if country_details:
                    for i in country_details:
                        dic = {
                            'id': i.id if i.id else None,
                            'name': i.name if i.name else None
                        }
                        country_list.append(dic)
                    msg = "Success"
                    success = True
                    return Response(json.dumps(
                        {"data": country_list, 'message': msg,
                         'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "Failed"
                    success = False
                    result = None
                    return Response(json.dumps(
                        {"data": result, 'message': msg, 'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)

            msg = "Token authentication failed"
            success = False
            result = None
            return Response(
                json.dumps({"data": result, 'message': msg, 'success': success},
                           sort_keys=True, indent=4, cls=ObjectEncoder),
                content_type='application/json;charset=utf-8', status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ############################# BRANCH SEARCH API ###################################################

    @http.route(['/api/search/branch'], auth="public", type='http', csrf=False)
    def search_branch(self, token=None, **kw):
        branch_list = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)

        try:
            if uid:
                branch_details = request.env['res.branch'].sudo().search([])
                if branch_details:
                    for i in branch_details:
                        dic = {
                            'id': i.id if i.id else None,
                            'name': i.name if i.name else None
                        }
                        branch_list.append(dic)
                    msg = "Success"
                    success = True
                    return Response(json.dumps(
                        {"data": branch_list, 'message': msg,'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "Failed"
                    success = False
                    result = None
                    return Response(json.dumps(
                        {"data": result, 'message': msg, 'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)

            msg = "Token authentication failed"
            success = False
            result = None
            return Response(
                json.dumps({"data": result, 'message': msg, 'success': success},
                           sort_keys=True, indent=4, cls=ObjectEncoder),
                content_type='application/json;charset=utf-8', status=202)

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    @http.route(['/api/point/of/sale/create/branch/<string:token>/'], auth="public", methods=['POST'], type='json', csrf=False)
    def create_branch(self, token, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            if uid:
                company = request.env['res.company'].sudo().search([('id','=',int(data['company_id']))])
                if company:
                    branch = request.env['res.branch'].sudo().create({
                        'name': data['name'],
                        'company_id':company.id,
                    })
                    msg = "Branch created Successfully"
                    success = True
                    return {'status': 200, 'message': msg, 'success': success, 'body': uid, 'branch_id': branch.id}
                else:
                    return {'status': 202, 'message': "Branch creation failed"}
            else:
                return {'status': 202, 'message': "Token Not In The System"}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ############################# SALESPERSON LIST API###################################################

    # @http.route('/api/salesperson/list', type='http', auth='user', methods=['GET'])
    # def get_sales_team_members(self, token=None, **kw):
    #     check_params({'token': token})
    #     ensure_db()
    #     env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
    #     uid = env['sfk_rest.token'].check_token(token)
    #     try:
    #         if uid:
    #             # Get the list of sales team members
    #             sales_team_group = request.env.ref('sales_team.group_sale_salesman')
    #             salesmen = request.env['res.users'].search([('groups_id', 'in', sales_team_group.id)])
    #
    #             # Create a list of dictionaries containing member information
    #             members_list = []
    #             for salesman in salesmen:
    #                 member_info = {
    #                     'id': salesman.id,
    #                     'name': salesman.name,
    #                     'email': salesman.login,
    #                     # Add other fields as needed
    #                 }
    #                 members_list.append(member_info)
    #
    #             # Return the data in JSON format
    #             response_data = {
    #                 'success': True,
    #                 'data': {
    #                     'members': members_list
    #                 }
    #             }
    #             return Response(json.dumps(response_data), content_type='application/json')
    #     except Exception as error:
    #         _logger.error(error)
    #         abort({'error': traceback.format_exc()}, rollback=True, status=400)

    @http.route('/api/salesperson/list/<string:token>/', auth="public", type='http', csrf=False)
    def get_sales_team_members(self, token, **kw):
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                sales_team_group = request.env.ref('sales_team.group_sale_salesman').sudo()
                salesmen = request.env['res.users'].sudo().search([('groups_id', 'in', sales_team_group.id)])
                members_list = []
                for salesman in salesmen:
                    member_info = {
                        'id': salesman.id,
                        'name': salesman.name,
                        'email': salesman.login,
                    }
                    members_list.append(member_info)
                response_data = {'data': members_list}
                return Response(json.dumps(response_data), content_type='application/json')
            else:
                return Response(
                    json.dumps(
                        {'message': "Token expired", 'success': "Failed",'status': 202},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                    content_type='application/json;charset=utf-8',
                    status=200)
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ####################################### Cart narration  ##############################################

    @http.route(['/api/create/cart/narration/<string:token>/'], auth="public",
                methods=['POST'], type='json', csrf=False)
    def create_cart_narration(self, token, **kwargs):
        try:
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            cart = request.env['sale.order'].sudo().search([('id', '=', int(data['cart_id']))])
            if uid:
                if cart:
                    cart.sudo().write({'narration': data.get('narration')})
                    return {'status': 200,
                            'message': 'Narration Added successfully.',
                            'cart_id': cart.id}
                else:
                    return {'status': 200,
                            'message': 'Cart not Found', 'success': False}
            else:
                return {'status': 202, 'message': 'Token Expired'}

        except KeyError as key_error:
            return {'status': 202,
                    'message': f"Missing required parameter: {str(key_error)}"}

        except Exception as error:
            _logger.error(error)
            return {'status': 400,
                    'message': 'An error occurred during narration'}

    ######################################### PAYMENT BANK OR CASH ########################################

    @http.route(['/api/make/payment/<string:token>/'], auth="public",
                type='json', methods=['POST'], csrf=False)
    def create_payment(self, token=None, **kw):
        check_params({'token': token})
        data = json.loads(request.httprequest.data)
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                customer = request.env['res.partner'].sudo().search(
                    [('id', '=', int(data['partner_id']))])
                cash_journal = request.env['account.journal'].sudo().search(
                    [('type', '=', 'cash')], limit=1)

                bank_journal = request.env['account.journal'].sudo().search(
                    [('type', '=', 'bank')], limit=1)

                if customer:
                    if data['journal_id'] == 'Bank':
                        payment = request.env['account.payment'].sudo().create({
                            "payment_type": "inbound",
                            "partner_id": customer.id,
                            "journal_id": bank_journal.id,
                            "amount": data["amount"],
                            "user_id": int(data['user_id'])
                        })
                        payment.action_post()
                    if data['journal_id'] == 'Cash':
                        payment = request.env['account.payment'].sudo().create({
                            "payment_type": "inbound",
                            "partner_id": customer.id,
                            "journal_id": cash_journal.id,
                            "amount": data["amount"],
                            "user_id": int(data['user_id'])
                        })
                        payment.action_post()
                    msg = "Success"
                    success = True
                    return {'status': 200, 'message': msg, 'success': success,
                            'body': uid}
                else:
                    msg = "Payment creation failed"
                    success = False
                    return {'status': 200, 'message': msg, 'success': success,
                            'body': uid}
            else:
                return {'status': 202, 'message': "Token Not In The System"}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    ######################################## API CURRENT DAY PAYMENT ###################################

    @http.route(['/api/today/all/payments'], auth="none", type='http', csrf=False)
    def show_payment(self, token, **kwargs):
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                today = fields.Date.today()
                payments = request.env['account.payment'].sudo().search(
                    [('state', "=", "posted"), ('date', '=', today)])
                payment_list = []
                total_payment_amount = []
                if payments:
                    total_payment = 0
                    for rec in payments:
                        total_payment += rec.amount
                        dic = {
                            'partner_id': rec.partner_id.name if rec.partner_id else None,
                            'date': str(rec.date) if rec.date else None,
                            'journal_id': rec.journal_id.name if rec.journal_id else None,
                            'name': rec.name if rec.name else None,
                            'amount': "{:.3f}".format(rec.amount) if rec.amount else None,
                            'branch_id': rec.branch_id.id if rec.branch_id else None,
                            'state': rec.state if rec.state else None,
                            "user_id": rec.user_id.name if rec.user_id else None,
                        }
                        payment_list.append(dic)
                    total_payment_amount.append(
                        {"total_payment": "{:.3f}".format(total_payment)})
                    msg = "Success"
                    success = True
                    return Response(
                        json.dumps(
                            {'data': [payment_list, total_payment_amount],
                             'message': msg, 'success': success},
                            sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "Payments not found"
                    success = False
                    return {'status': 200, 'message': msg,
                            'success': success,
                            'body': uid}
            else:
                return {'status': 202, 'message': 'Token Expired'}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True,
                  status=400)

    ####################################### WALKIN CUSTOMER LIST API ############################################
    @http.route(['/api/walkin/customer/list'], auth="none", type='http', csrf=False)
    def show_walkin_customer_list(self, token, **kwargs):
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                customer_list = []
                customer = request.env['res.partner'].sudo().search([('id', '=', request.env.ref('zcl_walkin_customer.walkin_customer_data').id)])
                if customer:
                    for rec in customer.walkin_customer_ids:
                        dic = {
                            'name': rec.name if rec.name else None,
                            'phone': rec.phone if rec.phone else None,
                        }
                        customer_list.append(dic)
                    msg = "Success"
                    success = True
                    return Response(
                        json.dumps(
                            {'data': customer_list,
                             'message': msg, 'success': success},
                            sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    return {'status': 202, 'message': 'Customer not found'}
            else:
                return {'status': 202, 'message': 'Token Expired'}

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True,
                  status=400)

    ######################################CREATE INVOICE ######################################################
    @http.route('/api/create_invoice/<string:token>/', auth='public', methods=['POST'], type='json',
                csrf=False)
    def create_invoice(self, token=None, **kw):
        try:
            check_params({'token': token})
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            if uid:
                sale_order = request.env['sale.order'].sudo().browse(int(data.get('sale_order_id')))
                if sale_order.state not in ['sale', 'done']:
                    return {'status': 400, 'message': 'Invalid sale order state for creating an invoice'}
                invoice = sale_order._create_invoices()
                return {'status': 200, 'message': 'Invoice created successfully', 'invoice_id': invoice.id}
            else:
                return {'status': 202, 'message': 'Token Expired'}
        except Exception as e:
            return {'status': 500, 'message': 'Error creating invoice', 'error': str(e)}

    ############################# SEARCH PRODUCT BY NAME #######################################
    @http.route(['/api/search/product/name'], auth="none", type='http', csrf=False)
    def show_product_list_name(self, token, **kwargs):
        ensure_db()
        data = json.loads(request.httprequest.data)
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                product_list = []
                product = request.env['product.product'].sudo().search([('name', 'ilike', str(data['name']))])
                if product:
                    for rec in product:
                        dic = {
                            'id': rec.id if rec.id else None,
                            'name': rec.name if rec.name else None,
                            'arabic_name': rec.product_tmpl_id.name_arabic if rec.product_tmpl_id.name_arabic else None,
                            'list_price': "{:.3f}".format(
                                rec.list_price) if rec.list_price else None,
                            'taxes_id': rec.taxes_id.ids if rec.taxes_id else None,
                            'item_group': rec.item_group.id if rec.item_group else None,
                            'item_sub_group': rec.item_sub_group.id if rec.item_sub_group else None,
                            'categ_id': rec.categ_id.id if rec.categ_id else None,
                        }
                        product_list.append(dic)
                    msg = "Success"
                    success = True
                    return Response(
                        json.dumps(
                            {'data': product_list,
                             'message': msg, 'success': success},
                            sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    return {'status': 202, 'message': 'Product not found'}
            else:
                return {'status': 202, 'message': 'Token Expired'}

        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    @http.route(['/api/search/all/products_with_price_list'], auth="public", type='http',
                csrf=False)
    def search_all_products_with_price_list(self, token=None, **kw):
        product_list = []
        check_params({'token': token})
        ensure_db()
        env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
        uid = env['sfk_rest.token'].check_token(token)
        try:
            if uid:
                price_list = request.env['price.category'].sudo().search([])
                user = request.env['res.users'].sudo().browse(uid).exists()
                # price_list = request.env['product.pricelist'].sudo().search([])
                if price_list:
                    for rec in price_list:
                        for res in rec.line_ids:
                            product_product = request.env[
                                'product.product'].sudo().search(
                                [('product_tmpl_id', '=', res.product_id.id)])
                            location_product = request.env[
                                'stock.quant'].sudo().search(
                                [('product_id', 'in', product_product.ids), ('location_id.branch_id', '=', user.branch_id.id)])
                            # on_hand_qty = sum(quant.quantity for quant in res.product_id.quant_ids)
                            for prod in location_product:
                                dic = {
                                    'product_id': prod.product_id.id if res.product_id.id else None,
                                    'product_name': prod.product_id.name if prod.product_id.name else None,
                                    # 'arabic_name': res.product_id.product_tmpl_id.name_arabic if res.product_id.product_tmpl_id.name_arabic else None,
                                    'product_code': res.product_code if res.product_code else None,
                                    'min_qty': prod.quantity if prod.quantity else None,
                                    'price': "{:.3f}".format(res.price),
                                    'box': res.product_id.box,
                                    'bag': res.product_id.bag,
                                    # 'start_date': res.date_start if res.date_start else None,
                                    # 'end_date': res.date_end if res.date_end else None,
                                    'price_list_name': rec.name,
                                    'price_list_id': rec.id,
                                    'category_id': res.product_id.categ_id.id if res.product_id.categ_id else None,
                                }
                                product_list.append(dic)
                    msg = "Success"
                    success = True
                    return Response(json.dumps(
                        {"data": product_list, 'message': msg,
                         'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=200)
                else:
                    msg = "No Price List Found"
                    success = False
                    result = None
                    return Response(json.dumps(
                        {"data": result, 'message': msg, 'success': success},
                        sort_keys=True, indent=4, cls=ObjectEncoder),
                        content_type='application/json;charset=utf-8',
                        status=202)
            else:
                msg = "Token authentication failed"
                success = False
                result = None
                return Response(json.dumps(
                    {"data": result, 'message': msg, 'success': success},
                    sort_keys=True, indent=4, cls=ObjectEncoder),
                    content_type='application/json;charset=utf-8',
                    status=202)
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

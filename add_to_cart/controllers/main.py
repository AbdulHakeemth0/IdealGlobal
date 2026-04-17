import os
import re
import json
import inspect
import logging
import tempfile
import datetime
import traceback
import requests
from werkzeug import exceptions
import base64
import io
from PIL import Image
from io import BytesIO
import odoo
from odoo import _
from odoo import tools
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
                        content_type='application/json;charset=utf-8', status=status)
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
    request._env = api.Environment(request.cr, uid, request.session.context or {})


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
        module = env['ir.module.module'].search([['name', '=', "sfk_rest"]], limit=1)
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
    def default(self, obj,item=None):
        def encode(item):
            if isinstance(item, models.BaseModel):
                vals = {}
                for name, field in item._fields.items():
                    if name in item:
                        if isinstance(item[name], models.BaseModel):
                            records = item[name]
                            if len(records) == 1:
                                vals[name] = (records.id, records.sudo().display_name)
                            else:
                                val = []
                                for record in records:
                                    val.append((record.id, record.sudo().display_name))
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

    @http.route([
        '/api/add/to/cart/<string:token>/'], auth="public", type='json', csrf=False)
    def add_to_carts(self, token, **post):
        print('ssssssssssssssssssssss')
        try:
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            product_line = []
            if uid and data:
                partner_id = int(data['partner_id'])
                carts = request.env['add.to.cart'].sudo().search([('partner_id', '=', partner_id)])
                for rec in data['order_line_ids']:
                    product = {
                        'product_id': rec['product_id'],
                        'qty': rec['qty'],
                        'image': rec['image'],
                        'unit_price': rec['unit_price'],
                        'price': rec['price']
                    }
                    product_line.append((0, 0, product))

                if carts:
                    carts.update({
                        'order_line_ids': product_line
                    })
                else:
                    carts = request.env['add.to.cart'].sudo().create({
                        'partner_id': data['partner_id'],
                        'country_id': data['country_id'],
                        'order_line_ids': product_line
                    })
                    print(carts,'ddddddddtttyyyyyyyy')
                return {'status': 200, 'message': "Success ", 'body': carts.id}
            else:
                if not uid:
                    body = "Token Expired "

                if not data:
                    body = "Data Is Null "

                return {'status': 202, 'message': body}
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    @http.route([
        '/api/add/to/cart/show/<string:token>/'], auth="public", type='http', csrf=False)
    def add_to_cart_show(self, token, partner_id=False, **kw):
        print('tdyqtcqtwxcwqcx')
        try:
            ensure_db()
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            product_list = []
            print(uid,'ttttttt')
            print(partner_id,'aaaaaaaaaaaaaaaa')
            if uid and partner_id:
                carts = request.env['add.to.cart'].sudo().search([('partner_id', '=', int(partner_id))])
                if carts:
                    for data in carts.order_line_ids:
                        dic = {
                            'cart_id': carts.id,
                            'product_id': data.product_id.id,
                            'name':data.product_id.name,
                            'description':data.product_id.description_sale,
                            'line_id': data.id,
                            'name': data.product_id.name,
                            'image': data.image,
                            'qty': data.qty,
                            'unit_price': data.unit_price,
                            'price': data.price
                        }
                        product_list.append(dic)
                else:
                    return Response(json.dumps({"status": 202, 'message': "No User With This Id"}))
                if product_list:
                    return Response(json.dumps({"data": product_list, 'message': "Success", 'success': True}, sort_keys=True, indent=4, cls=ObjectEncoder),
                                    content_type='application/json;charset=utf-8', status=200)
                else:
                    return Response(json.dumps({"status": 202, 'message': "No Product In Cart"}))
            else:
                if not partner_id:
                    body = "Partner Id Is Null"
                if not uid:
                    body = "Token Expired"
                return Response(json.dumps({"status": 202, 'message': body}))
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    @http.route([
        '/api/delete/cart/items/<string:token>/'], auth="public", type='http', csrf=False)
    def delete_cart_item(self, token, cart_id=False, line_id=False, **kw):
        try:
            ensure_db()
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            if uid and cart_id and line_id:
                order_line = request.env['add.to.cart.line'].sudo().search([('add_to_cart_id', '=', int(cart_id)), ('id', '=', int(line_id))])
                if order_line:
                    order_line.unlink()
                    return Response(json.dumps({"status": 200, 'message': "Successfully Unlinked"}))
                else:
                    return Response(json.dumps({"status": 202, 'message': "Not The Product In The System"}))
            else:
                if not cart_id:
                    body = "Cart Id Is Null"
                if not uid:
                    body = "Token Expired"
                if not line_id:
                    body = "Product Id Is Null"
                return Response(json.dumps({"status": 202, 'message': body}))
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    @http.route([
        '/api/delete/cart/<string:token>/'], auth="public", type='http', csrf=False)
    def delete_cart(self, token, cart_id=False, **kw):
        try:
            ensure_db()
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            if uid and cart_id:
                order = request.env['add.to.cart'].sudo().search(
                    [('id', '=', int(cart_id))])
                if order:
                    order.unlink()
                    return Response(json.dumps({"status": 200, 'message': "Successfully Unlinked"}))
                else:
                    return Response(json.dumps({"status": 202, 'message': "No Record In The System"}))
            else:
                if not cart_id:
                    body = "Cart Id Is Null"
                if not uid:
                    body = "Token Expired"
                return Response(json.dumps({"status": 202, 'message': body}))
        except Exception as error:
            _logger.error(error)
            abort({'error': traceback.format_exc()}, rollback=True, status=400)

    @http.route([
        '/api/product/update/<string:token>/'], auth="public", type='json', csrf=False)
    def add_product_update(self, token, **post):
        try:
            data = json.loads(request.httprequest.data)
            env = api.Environment(request.cr, odoo.SUPERUSER_ID, {})
            uid = env['sfk_rest.token'].check_token(token)
            if uid and data:
                order_line = request.env['add.to.cart.line'].sudo().search([('add_to_cart_id', '=', int(data['cart_id'])), ('id', '=', int(data['line_id']))])
                if order_line:
                    if data['image']:
                        order_line.write({
                            'image': data['image']
                        })
                    if data['qty']:
                        order_line.write({
                            'qty': int(data['qty'])
                        })
                    if data['price']:
                        order_line.write({
                            'price': int(data['price'])
                        })
                    if data['unit_price']:
                        order_line.write({
                            'unit_price': int(data['unit_price'])
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
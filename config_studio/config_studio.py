#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: hyy
@file: opc_modbus_tool
@time: 2020/06/8
@desc:

"""
import xlrd
import json
import re,functools
from pathlib import Path
from flask import Flask, request, render_template, Blueprint,session,url_for
from flask import Markup, make_response, jsonify, flash,current_app,redirect,g
from werkzeug.utils import secure_filename
import os
import time
from flask_wtf.csrf import generate_csrf
from uuid import uuid4
import linecache
import requests
from flask import Blueprint
import jwt
import datetime
from .forms import OpcForm,LoginForm,OpcdaForm
from instance.config import  client,server,opc,modbus,URL
from .model import User

"""
##################################### 基础配置 #########################################
"""


cs = Blueprint("cs", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent
log_path = os.path.join(BASE_DIR, 'logs')
conf_path = os.path.join(BASE_DIR, 'conf', '')

p = Path(conf_path)


"""
##################################### 公用方法 #########################################
"""
def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            form = LoginForm()
            return redirect(url_for('auth.login'))
            # return render_template('auth/login.html',form=form)

        return view(**kwargs)

    return wrapped_view

@cs.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = User.query.filter_by(id=user_id).first()



def check_day_log(start, end, logs, level, key):
    log_list = []
    log_day_start = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    log_day_end = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
    if key:
        log_list = search_log(key,logs)
        return log_list
        
    else:
        if end > start:
            for l in logs:
                log_day = datetime.datetime.strptime(
                    l.rsplit('  ')[0][1:-1], "%Y-%m-%d %H:%M:%S")
                log_level = l.rsplit('  ')[1][1:-1].strip(' ')
                # print(log_day_start,log_day,log_day_end,log_level,level)
                if log_day > log_day_start and log_day < log_day_end and log_level == level:
                    log_list.append(l.rsplit('  '))
                elif log_day > log_day_start and log_day < log_day_end and level == 'ALL':
                    log_list.append(l.rsplit('  '))
            return log_list
        else:
            return log_list


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'xls', 'xlsx'}


def search_log(key, logs,):
    logs_list = []
    if key[-1] == "*":
        for l in logs:
            print(key[:-1],l.rsplit('  ')[2][1:-1],)
            m = re.search('('+key[:-1]+')?', l.rsplit('  ')[2][1:-1])
            aa = m.group(0)
            if aa:
                logs_list.append(l.rsplit('  '))
        return logs_list
    else:
        for l in logs:
            if l.rsplit('  ')[2][1:-1] == key:
                logs_list.append(l.rsplit('  '))
        return logs_list


def search_tag(tagname, source, tag_list):
    if tagname[-1] == "*":
        for s in source:
            for ss in s:
                m = re.search('('+tagname[:-1]+')?', ss['tag'])
                aa = m.group(0)
                if aa:
                    tag_list.append(ss)
    else:
        for s in source:
            for ss in s:
                if ss['tag'] == tagname:
                    tag_list.append(ss)

    return tag_list


def read_json(module):
    json_name = conf_path+module[:-1]+'_run_config.json'
    cfg_msg = {}
    try:
        with open(json_name, 'r', encoding='utf-8') as f:
            cfg_msg = json.loads(f.read())
        return cfg_msg
    except Exception as e:
        print(str(e))
        return cfg_msg


def read_modbus_config(cfg_msg, module):
    tag_list = []
    basic_config = {}
    if cfg_msg:
        try:
            for d in cfg_msg["data"][module+'.data']:
                slave_id = d['slave_id']
                block = d['block']

                for b in block:
                    fun_code = b['fun_code']
                    tag_list.append(b['tags'])

            dev_id = cfg_msg["data"][module+'.dev_id']
            Coll_Type = cfg_msg["data"][module+'.Coll_Type']
            TCP = cfg_msg["data"][module+'.TCP']
            RTU = cfg_msg["data"][module+'.RTU']

            if Coll_Type == 'TCP':
                basic_config = {
                    'adev_id': dev_id,
                    'bColl_Type': Coll_Type,
                    'chost': TCP['host'],
                    'dport': TCP['port']
                }
            else:
                basic_config = {
                    'adev_id': dev_id,
                    'bColl_Type': Coll_Type,
                    'cserial': RTU['serial'],
                    'dbaud': RTU['baud'],
                    'edata_bit': RTU['data_bit'],
                    'fstop_bit': RTU['stop_bit'],
                    'gparity': RTU['parity'],
                }

            return tag_list, basic_config
        except Exception as e:
            print(str(e))
            return tag_list, basic_config
    else:
        return tag_list, basic_config


def read_opc_config(cfg_msg, module):
    opc_config = {}
    tag_list = []
    if cfg_msg:
        try:
            if module in client and cfg_msg:
                main_server_ip = cfg_msg['data'][module+'.main_server_ip']
                main_server_prgid = cfg_msg['data'][module +
                                                    '.main_server_prgid']
                main_server_clsid = cfg_msg['data'][module +
                                                    '.main_server_clsid']
                main_server_domain = cfg_msg['data'][module +
                                                     '.main_server_domain']
                main_server_user = cfg_msg['data'][module+'.main_server_user']
                main_server_password = cfg_msg['data'][module +
                                                       '.main_server_password']
                bak_server_ip = cfg_msg['data'][module+'.bak_server_ip']
                bak_server_prgid = cfg_msg['data'][module+'.bak_server_prgid']
                bak_server_clsid = cfg_msg['data'][module+'.bak_server_clsid']
                bak_server_domain = cfg_msg['data'][module +
                                                    '.bak_server_domain']
                bak_server_username = cfg_msg['data'][module +
                                                      '.bak_server_user']
                bak_server_password = cfg_msg['data'][module +
                                                      '.bak_server_password']

                opc_config = {
                    'main_server_ip': main_server_ip,
                    'main_server_progid': main_server_prgid,
                    'main_server_classid': main_server_clsid,
                    'main_server_domain': main_server_domain,
                    'main_server_username': main_server_user,
                    'main_server_password': main_server_password,
                    'bak_server_ip': bak_server_ip,
                    'bak_server_prgid': bak_server_prgid,
                    'bak_server_clsid': bak_server_clsid,
                    'bak_server_domain': bak_server_domain,
                    'bak_server_username': bak_server_username,
                    'bak_server_password': bak_server_password
                }
            else:
                enAutoTag = cfg_msg['data'][module+'.enAutoTag']
                isDataConvert = cfg_msg['data'][module+'.isDataConvert']
                opc_config = {
                    'enAutoTag': enAutoTag,
                    'isDataConvert': isDataConvert,
                }
            if module in ['s_opcda_client1', 's_opcda_client1', 's_opcda_client1']:
                for g in cfg_msg['data'][module+'.groups']:
                    group_id = g['group_id']
                    group_name = g['group_name']
                    collect_cycle = g['collect_cycle']
                    tag_list.append(g['tags'])
            return tag_list, opc_config
        except Exception as e:
            print(str(e), '-----------red opc config----------')
            return tag_list, opc_config
    else:
        return tag_list, opc_config


def decode_config(cfg_msg, module):
    if cfg_msg:
        tag_list = []

        header = cfg_msg[module[:-1]+'_run_config.json']
        if module in ['s_opcda_client1', 's_opcda_client2', 's_opcda_client3']:

            groups = header['groups']
            if groups:
                for g in eval(groups):
                    group_id = g['group_id']
                    group_name = g['group_name']
                    collect_cycle = g['collect_cycle']
                    tag_list.append(g['tags'])

            main_server_ip = header['main_server_ip']
            main_server_prgid = header['main_server_prgid']
            main_server_clsid = header['main_server_clsid']
            main_server_domain = header['main_server_domain']
            main_server_user = header['main_server_user']
            main_server_password = header['main_server_password']
            bak_server_ip = header['bak_server_ip']
            bak_server_prgid = header['bak_server_prgid']
            bak_server_clsid = header['bak_server_clsid']
            bak_server_domain = header['bak_server_domain']
            bak_server_username = header['bak_server_user']
            bak_server_password = header['bak_server_password']

            opc_config = {
                'main_server_ip': main_server_ip,
                'main_server_progid': main_server_prgid,
                'main_server_classid': main_server_clsid,
                'main_server_domain': main_server_domain,
                'main_server_username': main_server_user,
                'main_server_password': main_server_password,
                'bak_server_ip': bak_server_ip,
                'bak_server_prgid': bak_server_prgid,
                'bak_server_clsid': bak_server_clsid,
                'bak_server_domain': bak_server_domain,
                'bak_server_username': bak_server_username,
                'bak_server_password': bak_server_password,
                'groups': groups
            }

            return {'tag_list': tag_list, 'basic_config': opc_config}

        else:
            enAutoTag = header['enAutoTag']
            isDataConvert = header['isDataConvert']
            tag_list.append(header['tags'])
            opc_config = {
                'enAutoTag': enAutoTag,
                'isDataConvert': isDataConvert
            }

            return {'tags': tag_list, 'basic_config': opc_config}
    return {'tags': {}, 'basic_config': {}}


def call_s_config(ref_url, json_data):
    try:
        data = json.dumps(json_data)
        headers = {'content-type': 'application/json'}
        response = requests.post(
            url=ref_url, data=data, headers=headers, timeout=5)
        stu = False
        res = {}
        if response.status_code == 200 and response.json()["code"] == 1000:
            stu = True
            res = response.json()['data']
            return res, stu
        else:
            current_app.logger.debug(response.json()["msg"])
            return res, stu
    except Exception as error:
        current_app.logger.error(f'配置异常!原因:{error}')


@cs.route('/page', methods=['GET', 'POST'], endpoint='page')
def page():
    """
    分页
    """
    if request.method == 'POST':
        module = request.form['module']
        group = int(request.form['group'])-1
        pages = int(request.form['pages'])
        page = int(request.form['page'])
    else:

        module = request.args.get('module')
        group = int(request.args.get('group'))-1
        pages = int(request.args.get('pages'))  # 每页条目数10
        page = int(request.args.get('page'))  # 当前第几页1
    cfg_msg = read_json(module)
    if module in modbus:
        tags, basic_config = read_modbus_config(cfg_msg, module)
    else:
        tags, basic_config = read_opc_config(cfg_msg, module)
    total = 0
    if tags:
        groups = len(tags)  # 总计条目数
        for i in tags:
            total += len(i)
        max_pages, a = divmod(total, pages)
        if a > 0:
            max_pages = max_pages + 1
        # print(module, group, pages, page, groups, total, max_pages)
        start = (page-1) * pages
        end = page*pages
        data = tags[group][start:end]
        return {"tags": data, "basic_config": basic_config, "total": total, "max_pages": max_pages, 'groups': groups}
    return {"tags": [[]], "basic_config": basic_config, "total": 0, "max_pages": 0, 'groups': 0}


@cs.route('/search', methods=['GET', 'POST'], endpoint='search')
def search():
    """
    查找
    """
    module = request.args.get('module')
    tagname = request.args.get('tagname')  # 标签名
    cfg_msg = read_json(module)
    tags, basic_config = read_modbus_config(cfg_msg, module)
    data = search_tag(tagname, tags, [])
    current_app.logger.debug('查询位号:%s' % (tagname))
    return {"tags": data}


"""
##################################### config_setting ###############################

"""
@cs.route('/opc', methods=['GET', 'POST'], endpoint='opc')
def da_client():
    opc_ae_form = OpcForm()
    opc_da_form = OpcdaForm()
    return render_template('opc/da_ae_client.html',opc_ae_form=opc_ae_form,opc_da_form=opc_da_form)


@cs.route('/load_opc_se', methods=['GET', 'POST'], endpoint='load_opc_se')
@login_required
def load_opc_sev():
    if request.method == 'POST':
        module = request.form['module']
        enAutoTag = int(request.form['enAutoTag'])
        isDataConvert = int(request.form['isDataConvert'])
        tags = []
        if enAutoTag == 0:
            f = request.files['file']

            if f and allowed_file(f.filename):
                f.save(conf_path+secure_filename(f.filename))
            xl = list(p.rglob('opc.xlsx'))

            tag_key = ['publish_tag_name', 'write_able', 'data_type']
            write_able = 0
            data_type = 'ENUM_INT32'

            for T in xl:
                wb = xlrd.open_workbook(T)
                names = wb.sheet_names()
                tag = []
                for name in names:
                    st = wb.sheet_by_name(name)
                    nrows = st.nrows
                    tags_list = st.col_values(0, start_rowx=1, end_rowx=nrows)
                    for m in range(len(tags_list)):
                        publish_tag_name = tags_list[m]
                        tag_value = [publish_tag_name, write_able, data_type]
                        X = dict(zip(tag_key, tag_value))
                        tag.append(X)
            tags = tag
        basic_config = {module+'.enAutoTag': enAutoTag,
                        module+'.isDataConvert': isDataConvert}
        tags = {module+'.tags': tags}

        data = {**basic_config, **tags}

        res = {
            "module": "local",
            "data": data
        }
        with open(conf_path+"s_opcda_server_run_config.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(res, ensure_ascii=False,
                               sort_keys=False, indent=4))
        set_config(res, module)
        return render_template("opc/opc_show.html", basic_config=basic_config)

    return render_template("opc/opc_se_index.html",opc_da_server='bg-info')


@cs.route('/load_opc_da', methods=['GET', 'POST'], endpoint='load_opc_da')
@login_required
def load_opc_da():
    form = OpcForm()
    if request.method == 'POST':
        module = request.form['module']
        main_server_ip = request.form['main_server_ip']
        main_server_prgid = request.form['main_server_progid']
        main_server_clsid = request.form['main_server_classid']
        main_server_domain = request.form['main_server_domain']
        main_server_user = request.form['main_server_username']
        main_server_password = request.form['main_server_password']
        bak_server_ip = request.form['back_server_ip']
        bak_server_prgid = request.form['back_server_progid']
        bak_server_clsid = request.form['back_server_classid']
        bak_server_domain = request.form['back_server_domain']
        bak_server_user = request.form['back_server_username']
        bak_server_password = request.form['back_server_password']

        dict1 = {
            module+'.main_server_ip': main_server_ip,
            module+'.main_server_prgid': main_server_prgid,
            module+'.main_server_clsid': main_server_clsid,
            module+'.main_server_domain': main_server_domain,
            module+'.main_server_user': main_server_user,
            module+'.main_server_password': main_server_password,
            module+'.bak_server_ip': bak_server_ip,
            module+'.bak_server_prgid': bak_server_prgid,
            module+'.bak_server_clsid': bak_server_clsid,
            module+'.bak_server_domain': bak_server_domain,
            module+'.bak_server_user': bak_server_user,
            module+'.bak_server_password': bak_server_password
        }

        dict2 = {}
        f = request.files['file']

        if f and allowed_file(f.filename):
            f.save(conf_path+secure_filename(f.filename))
        xl = list(p.rglob('opc.xlsx'))

        group_key = ['group_id', 'group_name', 'collect_cycle', 'tags']
        collect_cycle = 10

        tag_key = ['tag_id', 'publish_tag_name',
                   'source_tag_name', 'data_type']
        source_tag_name = ''
        data_type = 'ENUM_INT32'

        for T in xl:
            wb = xlrd.open_workbook(T)
            names = wb.sheet_names()

            groups = []
            for name in names:
                tag = []
                st = wb.sheet_by_name(name)
                nrows = st.nrows

                tags_list = st.col_values(0, start_rowx=1, end_rowx=nrows)
                group_id = name.split('-', 1)[0][5:len(name.split('-', 1)[0])]
                group_name = name.split('-', 1)[0]
                collect_cycle = name.split('-', 1)[1]
                for m in range(len(tags_list)):
                    tag_id = m+(int(group_id)-1)*len(tags_list)
                    source_tag_name = tags_list[m]
                    publish_tag_name = source_tag_name
                    tag_value = [tag_id, publish_tag_name,
                                 source_tag_name, data_type]
                    X = dict(zip(tag_key, tag_value))
                    tag.append(X)

                tags = tag
                group_value = [group_id, group_name,
                               collect_cycle, tags]
                Y = dict(zip(group_key, group_value))
                groups.append(Y)

        dict2 = {module+'.groups': groups}
        data = {**dict1, **dict2}

        res = {
            "module": "local",
            "data": data
        }
        with open(conf_path+"s_opcda_client_run_config.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(res, ensure_ascii=False,
                               sort_keys=False, indent=4))
        cfg_msg = read_json(module)
        tags, basic_config = read_modbus_config(cfg_msg, module)
        set_config(res, module)
        return render_template("opc/opc_show.html", basic_config=dict1)
    return render_template("opc/opc_da_index.html",form=form,opc_da_client='bg-danger')


@ cs.route('/load_opc_ae', methods=['GET', 'POST'], endpoint='load_opc_ae')
@login_required
def load_opc_ae():
    if request.method == 'POST':

        module = request.form['module']
        main_server_ip = request.form['main_server_ip']
        main_server_prgid = request.form['main_server_progid']
        main_server_clsid = request.form['main_server_classid']
        main_server_domain = request.form['main_server_domain']
        main_server_user = request.form['main_server_username']
        main_server_password = request.form['main_server_password']
        bak_server_ip = request.form['back_server_ip']
        bak_server_prgid = request.form['back_server_progid']
        bak_server_clsid = request.form['back_server_classid']
        bak_server_domain = request.form['back_server_domain']
        bak_server_user = request.form['back_server_username']
        bak_server_password = request.form['back_server_password']

        dict1 = {
            module+'.main_server_ip': main_server_ip,
            module+'.main_server_prgid': main_server_prgid,
            module+'.main_server_clsid': main_server_clsid,
            module+'.main_server_domain': main_server_domain,
            module+'.main_server_user': main_server_user,
            module+'.main_server_password': main_server_password,
            module+'.bak_server_ip': bak_server_ip,
            module+'.bak_server_prgid': bak_server_prgid,
            module+'.bak_server_clsid': bak_server_clsid,
            module+'.bak_server_domain': bak_server_domain,
            module+'.bak_server_user': bak_server_user,
            module+'.bak_server_password': bak_server_password
        }

        dict2 = {
            module+".subscriptions":
            [{
                "subscription_id": 1,
                "subscription_name": "sub1",
                "enable": True,
                "update_rate": 1000,
                "max_size": 0,
                "event_type": "SIMPLE,TRACKING,CONDITION",
                "high_serverrity": 1000,
                "low_serverrity": 1
            }]}
        data = {**dict1, **dict2}
        res = {
            "module": "local",
            "data": data
        }
        with open(conf_path+"s_opcae_client_run_config.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(res, ensure_ascii=False,
                               sort_keys=False, indent=4))
        cfg_msg = read_json(module)
        tags, basic_config = read_modbus_config(cfg_msg, module)
        set_config(res, module)
        return render_template("opc/opc_show.html", basic_config=dict1)
    return render_template("opc/opc_ae_index.html",opc_ae_client='bg-warning')


@cs.route('/load_modbus', methods=['GET', 'POST'], endpoint='load_modbus')
@login_required
def load_modbus():
    if request.method == 'POST':
        module = request.form['module']
        dev_id = request.form['id']
        Coll_Type = request.form['type']
        host = request.form['ip']
        port = request.form['port']
        serial = request.form['com']
        baud = request.form['baud']
        data_bit = request.form['data_bit']
        stop_bit = request.form['stop_bit']
        parity = request.form['parity']

        dict1 = {
            module+'.dev_id': dev_id,
            module+'.Coll_Type': Coll_Type,
            module+'.TCP': {'host': host,
                            'port': port},
            module+'.RTU': {'serial': serial,
                            'baud': baud,
                            'data_bit': data_bit,
                            'stop_bit': stop_bit,
                            'parity': parity}
        }
        dict2 = {}
        f = request.files['file']
        data = []
        if f and allowed_file(f.filename):
            f.save(conf_path+secure_filename(f.filename))

            xl = list(p.rglob('modbus.xlsx'))
            for T in xl:
                wb = xlrd.open_workbook(T)
                names = wb.sheet_names()

            st = wb.sheet_by_name(names[0])
            nrows = st.nrows
            ncols = st.ncols
            d_type_1 = ['INT16', 'UINT16']
            d_type_2 = ['INT32', 'UINT32', 'FLOAT', 'DOUBLE']

            data_dict = {}
            block = []
            block_dict = {}
            tags = []

            for i in range(1, nrows):
                tags_list = st.row_values(i, start_colx=0, end_colx=None)
                tag = {
                    'tag': tags_list[0],
                    "start": int(tags_list[4]),
                    "register_number": 1 if tags_list[1] in d_type_1 else 2,
                    "data_type": tags_list[1],
                    "data_format": int(tags_list[5]),
                    "desc": tags_list[6],
                }
                slave_id = tags_list[2],
                fun_code = tags_list[3],
                tags.append(tag)

            block_dict = {'fun_code': int(fun_code[0]), 'tags': tags}
            block.append(block_dict)
            data_dict = {"slave_id": int(slave_id[0]), "block": block}
            data.append(data_dict)

        dict2 = {module+'.data': data}
        data = {**dict1, **dict2}
        res = {
            "module": "local",
            "data": data
        }
        with open(conf_path+"modbus_run_config.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(res, ensure_ascii=False,
                               sort_keys=False, indent=4))
        cfg_msg = read_json(module)
        tags, basic_config = read_modbus_config(cfg_msg, module)
        set_config(res, module)
        return render_template('opc/opc_show.html', basic_config=basic_config)
    return render_template('modbus/modbus_index.html',modbus_slave='bg-primary')


"""
##################################### 模块注册 #########################################

"""


@ cs.route('/module_reg', methods=['GET', 'POST'], endpoint='module_reg')
@login_required
def module_reg():
    return render_template('reg/register.html')


@ cs.route('/regist', methods=['GET', 'POST'], endpoint='regist')
def regist():
    if request.method == 'POST':
        print(request.form)
        # json_data = request.json
        # module = json_data['module']
        module = request.form['module']

        opc_server_config = {
            module[:-1]+"_run_config.json": {
                "enAutoTag": "int",
                "isDataConvert": "int",
                "tags": "list"
            }
        }
        opc_da_client_config = {
            module[:-1]+"_run_config.json": {
                "main_server_ip": "string",
                "main_server_prgid": "string",
                "main_server_clsid": "string",
                "main_server_domain": "string",
                "main_server_user": "string",
                "main_server_password": "string",
                "bak_server_ip": "string",
                "bak_server_prgid": "string",
                "bak_server_clsid": "string",
                "bak_server_domain": "string",
                "bak_server_user": "string",
                "bak_server_password": "string",
                "groups": "list"
            }
        }
        opc_ae_client_config = {
            module[:-1]+"_run_config.json": {
                "main_server_ip": "string",
                "main_server_prgid": "string",
                "main_server_clsid": "string",
                "main_server_domain": "string",
                "main_server_user": "string",
                "main_server_password": "string",
                "bak_server_ip": "string",
                "bak_server_prgid": "string",
                "bak_server_clsid": "string",
                "bak_server_domain": "string",
                "bak_server_user": "string",
                "bak_server_password": "string",
                "subscriptions": "list"
            }
        }
        modbus_config = {
            module[:-1]+"_run_config.json": {
                "dev_id": "string",
                "Coll_Type": "string",
                "TCP": {
                    "host": "string",
                    "port": "string"
                },
                "RTU": {
                    "serial": "string",
                    "baud": "string",
                    "data_bit": "string",
                    "stop_bit": "string",
                    "parity": "string"
                },
                "data": "list",
            }
        }
        modules = {'s_opcda_server': opc_server_config,
                   's_opcae_server': '',
                   's_opcda_client': opc_da_client_config,
                   's_opcae_client': opc_ae_client_config,
                   'modbus': modbus_config}
        config = modules.get(module[:-1], '')
        print(config)
        # if module in server:

        #     json_data = {
        #         "module": request.form['module'],
        #         "url": request.form['resful_url'],
        #         "config":  opc_server_config
        #     }
        # else:
        #     json_data = {
        #         "module": request.form['module'],
        #         "url": request.form['resful_url'],
        #         "config":  opc_da_client_config
        #     }
        json_data = {
            "module": request.form['module'],
            "url": request.form['resful_url'],
            "config":  config
        }
        res, stu = call_s_config(URL['regist_url'], json_data)
        if stu:
            current_app.logger.debug(f'{module}模块注册成功')
            return {'success': True, 'msg': f'{module}模块注册成功'}
        else:
            current_app.logger.debug(f'{module}模块注册失败')
            return {'success': True, 'msg': f'{module}模块注册失败'}

    return render_template('reg/register.html')


@ cs.route('/unregist', methods=['GET', 'POST'], endpoint='unregist')
def unregist():
    if request.method == 'POST':
        json_data = request.json
        module = json_data['module']
        res, stu = call_s_config(URL['unregist_url'], json_data)
        if stu:
            current_app.logger.debug(f'{module}模块注销成功')
            return {'success': True, 'msg': f'{module}模块注销成功'}
        else:
            current_app.logger.debug(f'{module}模块注销失败')
            return {'success': True, 'msg': f'{module}模块注销失败'}

    return render_template('reg/register.html')


"""
##################################### review_config ################################

"""


@ cs.route('/alter_module', methods=['GET', 'POST'], endpoint='alter_module')
def alter_module():

    module = request.args.get('module')
    cfg_msg = read_json(module)
    if module in opc:
        tags, basic_config = read_opc_config(cfg_msg, module)
        current_app.logger.debug(f'开始编辑{module}基础配置')
    else:
        tags, basic_config = read_modbus_config(cfg_msg, module)
        current_app.logger.debug(f'开始编辑{module}基础配置')
    return {'basic_config': basic_config}


@ cs.route('/config_review', methods=['GET', 'POST'], endpoint='config_review')
@login_required
def config_review():
    if request.method == 'POST':
        module = request.form['module']
        cfg_msg = read_json(module)
        if module in opc:
            tags, basic_config = read_opc_config(cfg_msg, module)
            current_app.logger.debug(f'查看{module}基础配置')
        else:
            tags, basic_config = read_modbus_config(cfg_msg, module)
            current_app.logger.debug(f'查看{module}基础配置')
        return {'basic_config': basic_config}

    module = 's_opcda_client1'
    cfg_msg = read_json(module)
    if module in opc:
        tags, basic_config = read_opc_config(cfg_msg, module)
    else:
        tags, basic_config = read_modbus_config(cfg_msg, module)
    return render_template('opc/opc_show.html', basic_config=basic_config,config_review='bg-success')


@ cs.route('/tags_review/', methods=['GET', 'POST'], endpoint='tags_review')
@login_required
def tags_review():
    if request.method == 'POST':
        module = request.form['module']
        cfg_msg = read_json(module)
        if module in opc:
            tags, basic_config = read_opc_config(cfg_msg, module)
            current_app.logger.debug(f'查看{module}位号配置')
        else:
            tags, basic_config = read_modbus_config(cfg_msg, module)
            current_app.logger.debug(f'查看{module}位号配置')
        return {'tags': tags}

    # module1 = request.args.get('module')
    module = 's_opcda_client1'
    cfg_msg = read_json(module)
    if module in opc:
        tags, basic_config = read_opc_config(cfg_msg, module)
    else:
        tags, basic_config = read_modbus_config(cfg_msg, module)
    return render_template('opc/opc_tags.html', tags=tags,tags_review='bg-danger')


@ cs.route('/get_config', methods=['GET', 'POST'], endpoint='get_config')
@login_required
def get_config():
    if request.method == 'POST':
        res_msg = {}
        module = request.form['module']
        json_data = {'module': module}
        res, stu = call_s_config(URL['getconfig_url'], json_data)
        if stu:
            res_msg = decode_config(res, module)

            user_name=g.user.username
            current_app.logger.debug(f'用户{user_name}:获取{module}模块配置成功')
            return res_msg
        else:
            current_app.logger.debug(f'获取{module}模块配置失败{res}')
            return res_msg

    return '不支持的方法'


def set_config(cfg_msg, module):
    if request.method == 'POST':
        res, stu = call_s_config(URL['setconfig_url'], cfg_msg)
        if stu:
            current_app.logger.debug(f'{module}模块配置成功')
        else:
            current_app.logger.debug(f'{module}模块配置失败{res}')
    return '不支持的方法'


"""
##################################### 日志 ###########################################

"""


@ cs.route('/log', methods=['GET', 'POST'], endpoint='log')
@login_required
def logs():
    if request.method == 'POST':
        logs_list = []
        log_level = request.form.get('log_level', 'ALL')
        log_day = request.form.get('log_day', time.strftime('%Y-%m-%d'))
        log_day_start = log_day+' ' + \
            request.form.get('log_day_start', '00:00:00')
        log_day_end = log_day+' '+request.form.get("log_day_end", "23:59:59")
        pages = int(request.form.get('pages', 5))
        page = int(request.form.get('page', 1))
        key = request.form.get('key')
        log_name = log_path+'\\'+'{}.log'.format(log_day)
        if not all((log_day, log_day_start, log_day_end)):
            return {'logs_list': [], 'total': 0, 'max_pages': 0, 'msg': f'请输入查询日期和时间'}
        try:
            with open(log_name, 'r', encoding='utf-8') as lg:
                logs = lg.read().splitlines()
        except Exception as e:
            return {'logs_list': [], 'total': 0, 'max_page': 0, 'msg': f'OOOPS..[{log_day}]没有日志,被外星人偷走了？？'}
        text = linecache.getline(log_name, 2)[1:-1]
        logs_list = check_day_log(
            log_day_start, log_day_end, logs, log_level, key)
        data, total, max_pages = [], 0, 0
        # print(len(logs_list))
        if logs_list:
            total = len(logs_list)  # 总计条目数
            max_pages, a = divmod(total, pages)
            if a > 0:
                max_pages = max_pages + 1
            # print(pages, page, total, max_pages)
            start = (page-1) * pages
            end = page*pages
            data = logs_list[start:end]
            return {'logs_list': data, 'total': total, 'max_pages': max_pages, 'msg': f'查询到{total}条日志'}
        else:
            return {'logs_list': data, 'total': total, 'max_pages': max_pages, 'msg': f'查询到{total}条日志'}

    else:
        logs_list = []
        with open(log_path+'\\'+'{}.log'.format(time.strftime('%Y-%m-%d')), 'r', encoding='utf-8') as lg:
            logs = lg.read().splitlines()
        for l in logs:
            logs_list.append(l.rsplit('  '))
        return render_template('log/log.html', logs_list=logs_list[:4],log='bg-info')

def log1():
    loglevel = []
    for root, dirs, files in os.walk(log_path):
        loglist = files
    for lv in loglist:
        loglevel.append(lv.split('-')[0])
    dicts = dict(zip(loglevel, loglist))
    current_app.logger.debug('访问日志系统.')
   
def check_log():
    if request.method == "GET":
        log_level = request.args.get("log_level")
        log_day = request.args.get("log_day")
        log_list = []
        for root, dirs, files in os.walk(log_path):
            loglist = files
        for lv in loglist:
            if lv.split('-')[0] == log_level and lv == log_level+'-'+log_day+'.log':
                log_list.append(lv)
            elif lv.split('-')[0] == log_level and log_day == '':
                log_list.append(lv)
        return {'log_level': log_level, 'log_list': log_list}




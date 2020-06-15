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
import re
from pathlib import Path
from flask import Flask, request, render_template, Blueprint, Markup, make_response, jsonify, flash
from werkzeug.utils import secure_filename
import os
import time
from flask_wtf.csrf import generate_csrf
from uuid import uuid4
import linecache
import requests
from flask import Blueprint
from config_studio import conf_path, log_path, log
import jwt
import datetime

"""
##################################### 基础配置 #########################################
"""


cs = Blueprint("cs", __name__)


p = Path(conf_path)


# regist_url = 'http://127.0.0.1:40200/s_config/v1.0/regist_config'
# unregist_url = 'http://127.0.0.1:40200/s_config/v1.0/unregist_config'
# getconfig_url = 'http://127.0.0.1:40200/s_config/v1.0/get_configs'
# setconfig_url = 'http://127.0.0.1:40200/s_config/v1.0/set_configs'

regist_url = 'http://192.168.20.213:40200/s_config/v1.0/regist_config'
unregist_url = 'http://192.168.20.213:40200/s_config/v1.0/unregist_config'
getconfig_url = 'http://192.168.20.213:40200/s_config/v1.0/get_configs'
setconfig_url = 'http://192.168.20.213:40200/s_config/v1.0/set_configs'

client = [
    's_opcda_client1',
    's_opcda_client2',
    's_opcda_client3',
    's_opcae_client1',
    's_opcae_client2',
    's_opcae_client3'
]

server = ['s_opcda_server1',
          's_opcda_server2',
          's_opcda_server3']
opc = [
    's_opcda_server1',
    's_opcda_server2',
    's_opcda_server3',
    's_opcda_client1',
    's_opcda_client2',
    's_opcda_client3',
    's_opcae_client1',
    's_opcae_client2',
    's_opcae_client3'
]

modbus = ['modbus1', 'modbus2']


"""
##################################### 公用方法 #########################################
"""


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'xls', 'xlsx'}


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
            print(str(e), '---------------------------')
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
            log.debug(response.json()["msg"])
            return res, stu
    except Exception as error:
        log.error(f'配置异常!原因:{error}')


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
    log.debug('查询位号:%s' % (tagname))
    return {"tags": data}


"""
##################################### config_setting ###############################

"""


@cs.route('/load_opc_se', methods=['GET', 'POST'], endpoint='load_opc_se')
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
    return render_template("opc/opc_se_index.html")


@cs.route('/load_opc_da', methods=['GET', 'POST'], endpoint='load_opc_da')
def load_opc_da():
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
    return render_template("opc/opc_da_index.html")


@ cs.route('/load_opc_ae', methods=['GET', 'POST'], endpoint='load_opc_ae')
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
    return render_template("opc/opc_ae_index.html")


@cs.route('/load_modbus', methods=['GET', 'POST'], endpoint='load_modbus')
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
    return render_template('modbus/modbus_index.html')


"""
##################################### 模块注册 #########################################

"""


@ cs.route('/module_reg', methods=['GET', 'POST'], endpoint='module_reg')
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
        res, stu = call_s_config(regist_url, json_data)
        if stu:
            log.debug(f'{module}模块注册成功')
            return {'success': True, 'msg': f'{module}模块注册成功'}
        else:
            log.debug(f'{module}模块注册失败')
            return {'success': True, 'msg': f'{module}模块注册失败'}

    return render_template('reg/register.html')


@ cs.route('/unregist', methods=['GET', 'POST'], endpoint='unregist')
def unregist():
    if request.method == 'POST':
        json_data = request.json
        module = json_data['module']
        res, stu = call_s_config(unregist_url, json_data)
        if stu:
            log.debug(f'{module}模块注销成功')
            return {'success': True, 'msg': f'{module}模块注销成功'}
        else:
            log.debug(f'{module}模块注销失败')
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
        log.info(f'开始编辑{module}基础配置')
    else:
        tags, basic_config = read_modbus_config(cfg_msg, module)
        log.info(f'开始编辑{module}基础配置')
    return {'basic_config': basic_config}


@ cs.route('/config_review', methods=['GET', 'POST'], endpoint='config_review')
def config_review():
    if request.method == 'POST':
        module = request.form['module']
        cfg_msg = read_json(module)
        if module in opc:
            tags, basic_config = read_opc_config(cfg_msg, module)
            log.debug(f'查看{module}基础配置')
        else:
            tags, basic_config = read_modbus_config(cfg_msg, module)
            log.debug(f'查看{module}基础配置')
        return {'basic_config': basic_config}

    module = 's_opcda_client1'
    cfg_msg = read_json(module)
    if module in opc:
        tags, basic_config = read_opc_config(cfg_msg, module)
    else:
        tags, basic_config = read_modbus_config(cfg_msg, module)
    return render_template('opc/opc_show.html', basic_config=basic_config)


@ cs.route('/tags_review/', methods=['GET', 'POST'], endpoint='tags_review')
def tags_review():
    if request.method == 'POST':
        module = request.form['module']
        cfg_msg = read_json(module)
        if module in opc:
            tags, basic_config = read_opc_config(cfg_msg, module)
            log.debug(f'查看{module}位号配置')
        else:
            tags, basic_config = read_modbus_config(cfg_msg, module)
            log.debug(f'查看{module}位号配置')
        return {'tags': tags}

    # module1 = request.args.get('module')
    module = 's_opcda_client1'
    cfg_msg = read_json(module)
    if module in opc:
        tags, basic_config = read_opc_config(cfg_msg, module)
    else:
        tags, basic_config = read_modbus_config(cfg_msg, module)
    return render_template('opc/opc_tags.html', tags=tags)


@ cs.route('/get_config', methods=['GET', 'POST'], endpoint='get_config')
def get_config():
    if request.method == 'POST':
        res_msg = {}
        module = request.form['module']
        json_data = {'module': module}
        res, stu = call_s_config(getconfig_url, json_data)
        if stu:
            res_msg = decode_config(res, module)
            log.debug(f'获取{module}模块配置成功{res_msg}')
            return res_msg
        else:
            log.debug(f'获取{module}模块配置失败{res}')
            return res_msg

    return '不支持的方法'


def set_config(cfg_msg, module):
    if request.method == 'POST':
        res, stu = call_s_config(setconfig_url, cfg_msg)
        if stu:
            log.debug(f'{module}模块配置成功')
        else:
            log.debug(f'{module}模块配置失败{res}')
    return '不支持的方法'


"""
##################################### 日志 ###########################################

"""


@ cs.route('/log', methods=['GET', 'POST'], endpoint='log')
def logs():
    logs_list = []
    with open(log_path+'\\'+'{}.log'.format(time.strftime('%Y-%m-%d')), 'r', encoding='utf-8') as rf:
        logs = rf.read().splitlines()
    text = linecache.getline(
        log_path+'\\'+'{}.log'.format(time.strftime('%Y-%m-%d')), 2)
    print(text)
    for log in logs:
        logs_list.append(log.rsplit(' '))
    return render_template('log/log.html', logs=logs_list)


@ cs.route('/log1', methods=['GET', 'POST'], endpoint='log1')
def log1():
    loglevel = []
    for root, dirs, files in os.walk(log_path):
        loglist = files
    for lv in loglist:
        loglevel.append(lv.split('-')[0])
    dicts = dict(zip(loglevel, loglist))
    log.debug('注意!'+'在' + time.strftime('%Y-%m-%d %H:%M:%S')+'访问日志系统.')
    return render_template('log/logs.html', **{'dicts': dicts, 'log_level': loglevel})


# 日志查询
@ cs.route('/check_log', methods=['GET', 'POST'], endpoint='check_log')
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


# 日志展示
@ cs.route('/show_log', methods=['GET', 'POST'], endpoint='show_log')
def show_log():
    response = {}
    if request.method == "GET":
        try:
            log_level = request.args.get("log_level")
            log_name = request.args.get("log_name")
            filename = os.path.join(log_path, log_name),  # 返回元组
            with open(filename[0], 'r', encoding='UTF-8') as f:
                log_text = f.readlines()

            text = linecache.getline(filename[0], 2)

            if len(log_text) == 0:
                log_text.append("暂无日志")
            response['log_level'] = log_level
            response['log_text'] = log_text
            response['msg'] = 'success'
            response['code'] = 200
            response["Access-Control-Allow-Origin"] = "*"
        except Exception as e:
            response['msg'] = str(e)
            response['error_num'] = 1000
        return response


"""
##################################### 集成vue ########################################

"""


@ cs.route('/vue', methods=['GET', 'POST'], endpoint='vue')
def vue():
    if request.method == 'POST':
        cs.logger.debug('flask debug')
        name = request.json.get("name")
        age = request.json.get("age")
        csrf_token = generate_csrf()
        res = {
            'data': [
                {'id': 1, 'name': name, 'age': age},
                {'id': 2, 'name': name, 'age': age},
                {'id': 2, 'name': name, 'age': age},
                {'id': 2, 'name': name, 'age': age}
            ],
            'status': 200,
            'msg': 'OK',
            'headers': {"X-CSRFToken": csrf_token, "Access-Control-Allow-Origin": "*"},
            'config': {}
        }
        response = make_response(jsonify(res))
        # 设置响应请求头
        response.headers["Access-Control-Allow-Origin"] = '*'
        response.headers["Access-Control-Allow-Methods"] = 'POST'
        response.headers["Access-Control-Allow-Headers"] = "x-requested-with,content-type"

        # return json.dumps(res)
        log.info('info 请求')
        log.debug('debug 请求')
        return response
    print(request.args.get('id'), request.args.get('name'))
    res = {
        'groceryList': [
            {'id': 0, 'text': '蔬菜'},
            {'id': 1, 'text': '奶酪'},
            {'id': 2, 'text': '随便其它什么人吃的东西'}
        ],
        'status': 1000,
        'statusText': 'OK',
        'headers': {},
        'config': {}
    }
    return render_template('vue/vue.html', res=res)


if __name__ == "__main__":
    cs.run(host='127.0.0.1', port='80', debug=True)

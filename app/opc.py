#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: hyy
@file: opc_modbus_tool
@time: 2020/06/8
@desc:

"""
import datetime
import os
import time
import xlrd
import json
import re
import functools
import linecache
import requests
from flask import request, render_template, Blueprint, session, url_for
from flask import current_app, redirect, g
from werkzeug.utils import secure_filename
from .forms import OpcForm, OpcdaForm
from .config import client, opc, modbus, URL
from .model import User
from .settings import Config
from .zmq_sensor import SensorClient, sensor2dict
from .zmq_event import EventClient, event2dict
import psutil
import signal
from app.utils import paginate


cs = Blueprint("cs", __name__)

conf_path = Config.conf_path
log_path = Config.log_path
p = Config.p


"""
##################################### 公用方法 #########################################
"""


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
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


def kill_python(p_name, p_pid=None):
    for proc in psutil.process_iter():
        if proc.name() == "python.exe":
            print(proc.cmdline())
            if proc.cmdline()[1] == 'p_name':
                print(proc.cmdline(), proc.pid)
                os.kill(proc.pid, signal.SIGINT)


def kill_process(pid):
    try:
        a = os.kill(pid, signal.SIGINT)
        if not a:
            current_app.logger.debug(f'已经结束pid为{pid}的进程')
            return True
    except OSError as e:
        current_app.logger.debug('没有如此进程!!!')
        return False


def check_day_log(start, end, logs, level, key):
    log_list = []
    log_day_start = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    log_day_end = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
    if key:
        log_list = search_log(key, logs)
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
            print(key[:-1], l.rsplit('  ')[2][1:-1],)
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


def search_modbus_tag(tagname, source, tag_list):
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


def search_opc_tag(tagname, source, tag_list):
    if tagname[-1] == "*":
        for s in source:
            for ss in s:
                m = re.search('('+tagname[:-1]+')?', ss['publish_tag_name'])
                aa = m.group(0)
                if aa:
                    tag_list.append(ss)
    else:
        for s in source:
            for ss in s:
                if ss['publish_tag_name'] == tagname:
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
    group_infos = []
    if cfg_msg:
        try:
            dev_id = cfg_msg["data"][module+'.dev_id']
            Coll_Type = cfg_msg["data"][module+'.Coll_Type']
            TCP = cfg_msg["data"][module+'.TCP']
            RTU = cfg_msg["data"][module+'.RTU']

            if Coll_Type == 'TCP':
                basic_config = {
                    'dev_id': dev_id,
                    'Coll_Type': Coll_Type,
                    'host': TCP['host'],
                    'port': TCP['port']
                }
            else:
                basic_config = {
                    'dev_id': dev_id,
                    'Coll_Type': Coll_Type,
                    'serial': RTU['serial'],
                    'baud': RTU['baud'],
                    'data_bit': RTU['data_bit'],
                    'stop_bit': RTU['stop_bit'],
                    'parity': RTU['parity'],
                }
            i = 1
            for data in cfg_msg["data"][module+'.data']:
                slave_id = data['slave_id']
                for d_b in data['block']:
                    fun_code = d_b['fun_code']
                    tag_list.append(d_b['tags'])
                    group_info = {'group_id': i, 'slave_id': slave_id, 'group_name': fun_code,
                                  'collect_cycle': 5, 'tags_num': len(d_b['tags']), 'tags': d_b['tags']}
                    group_infos.append(group_info)
                    i += 1
            return tag_list, basic_config, group_infos
        except Exception as e:
            print(str(e), '------error in read modbus conf----------')
            return tag_list, basic_config, group_infos
    else:
        return tag_list, basic_config, group_infos


def read_opc_config(cfg_msg, module):
    opc_config = {}
    tag_list = []
    group_infos = []
    if cfg_msg:
        try:
            if module in client:
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
                bak_server_user = cfg_msg['data'][module +
                                                  '.bak_server_user']
                bak_server_password = cfg_msg['data'][module +
                                                      '.bak_server_password']

                opc_config = {
                    'main_server_ip': main_server_ip,
                    'main_server_prgid': main_server_prgid,
                    'main_server_clsid': main_server_clsid,
                    'main_server_domain': main_server_domain,
                    'main_server_user': main_server_user,
                    'main_server_password': main_server_password,
                    'bak_server_ip': bak_server_ip,
                    'bak_server_prgid': bak_server_prgid,
                    'bak_server_clsid': bak_server_clsid,
                    'bak_server_domain': bak_server_domain,
                    'bak_server_user': bak_server_user,
                    'bak_server_password': bak_server_password
                }
            else:
                enAutoTag = cfg_msg['data'][module+'.enAutoTag']
                isDataConvert = cfg_msg['data'][module+'.isDataConvert']
                opc_config = {
                    'enAutoTag': enAutoTag,
                    'isDataConvert': isDataConvert,
                }
            if module in client:
                for g in cfg_msg['data'][module+'.groups']:
                    group_id = g['group_id']
                    group_name = g['group_name']
                    collect_cycle = g['collect_cycle']
                    group_info = {'group_id': group_id, 'group_name': group_name,
                                  'collect_cycle': collect_cycle, 'tags_num': len(g['tags']), 'tags': g['tags']}
                    tag_list.append(g['tags'])
                    group_infos.append(group_info)
            return tag_list, opc_config, group_infos
        except Exception as e:
            print(str(e), '--------error  in read opc config----------')
            return tag_list, opc_config, group_infos
    else:
        return tag_list, opc_config, group_infos


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
                'main_server_prgid': main_server_prgid,
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
    stu = False
    res = {}
    try:
        data = json.dumps(json_data)
        headers = {'content-type': 'application/json'}
        response = requests.post(
            url=ref_url, data=data, headers=headers, timeout=5)
        if response.status_code == 200 and response.json()["code"] == 1000:
            stu = True
            res = response.json()['data']
            return res, stu
        else:
            current_app.logger.debug(response.json()["msg"])
            return res, stu
    except Exception as error:
        current_app.logger.error(f'配置异常!原因:{error}')
        return res, stu

# 废弃
@cs.route('/page', methods=['GET', 'POST'], endpoint='page')
def page():
    """
    分页
    """
    group_infos = []
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
        tags, basic_config, group_infos = read_modbus_config(cfg_msg, module)
    else:
        tags, basic_config, group_infos = read_opc_config(cfg_msg, module)
    total = 0
    if tags:
        groups = len(tags)  # 总计条目数
        for i in tags:
            total += len(i)
        max_pages, a = divmod(total, pages)
        has_pre = False
        has_next = False

        if a > 0:
            max_pages = max_pages + 1

        if page != 1:
            has_pre = True
        if page != max_pages:
            has_next = True

        # print(module, group, pages, page, groups, total, max_pages)
        start = (page-1) * pages
        end = page*pages
        data = tags[group][start:end]
        return {"tags": data, "basic_config": basic_config, "group_infos": group_infos, "total": total, "max_pages": max_pages, 'groups': groups}
    return {"tags": [[]], "basic_config": basic_config, "group_infos": [], "total": 0, "max_pages": 0, 'groups': 0}


@cs.route('/show_tag_page', methods=['GET', 'POST'], endpoint='show_tag_page')
def show_tag_page():
    group_infos = []
    if request.method == 'POST':
        group_id = int(request.form.get('group_id', 1))-1
        module = request.form.get('module', 's_opcda_client1')
        pages = int(request.form.get('pages', 10))
        page = int(request.form.get('page', 1))
        # print(group_id, module, pages, page)
        cfg_msg = read_json(module)
        if module in modbus:
            tags, basic_config, group_infos = read_modbus_config(
                cfg_msg, module)
        else:
            tags, basic_config, group_infos = read_opc_config(cfg_msg, module)
        if group_infos:
            pga = paginate(group_infos[group_id]['tags'], page, pages)
            return {"paginate": pga, 'group_infos': group_infos, 'module': module}
        return {"paginate": [], 'group_infos': [], 'module': module}

    module = str(request.args.get('module', 's_opcda_client1'))
    pages = int(request.args.get('pages', 10))
    page = int(request.args.get('page', 1))

    cfg_msg = read_json(module)
    if module in modbus:
        tags, basic_config, group_infos = read_modbus_config(
            cfg_msg, module)
    else:
        tags, basic_config, group_infos = read_opc_config(cfg_msg, module)
    pga = paginate(group_infos, page, pages)

    return render_template('opc/show_tag.html', paginate=pga, group_infos=group_infos, group='bg-info')

# 废弃
@cs.route('/search', methods=['GET', 'POST'], endpoint='search')
def search():
    """
    查找
    """
    module = request.args.get('module')
    tagname = request.args.get('tagname')  # 标签名
    cfg_msg = read_json(module)
    if module in modbus:
        tags, basic_config, group_infos = read_modbus_config(cfg_msg, module)
        data = search_modbus_tag(tagname, tags, [])
    else:
        tags, basic_config, group_infos = read_opc_config(cfg_msg, module)
        data = search_opc_tag(tagname, tags, [])
    current_app.logger.debug(f'查询{module}位号:%s' % (tagname))
    return {"tags": data}


@cs.route('/show_tag_search', methods=['GET', 'POST'], endpoint='show_tag_search')
def show_tag_search():
    """
    查找
    """
    group_id = int(request.args.get('group_id', 1))-1
    pages = int(request.form.get('pages', 10))
    page = int(request.form.get('page', 1))
    module = request.args.get('module')
    tagname = request.args.get('tagname')
    cfg_msg = read_json(module)
    if module in modbus:
        tags, _, group_infos = read_modbus_config(cfg_msg, module)
        data = search_modbus_tag(tagname, tags, [])
    else:
        tags, _, group_infos = read_opc_config(cfg_msg, module)
        data = search_opc_tag(tagname, tags, [])

    pga = paginate(data, page, pages)

    current_app.logger.debug(f'查询{module}位号:%s' % (tagname))
    return {"paginate": pga, 'group_infos': group_infos}


@cs.route('/add_group', methods=['GET', 'POST'], endpoint='add_group')
def add_group():
    module = request.form.get('module')
    group_name = request.form.get('group_name')
    collect_cycle = int(request.form.get('collect_cycle'))
    print(module, group_name, collect_cycle)
    cfg_msg = read_json(module)
    if module in modbus:
        tags, basic_config, group_infos = read_modbus_config(cfg_msg, module)
    else:
        tags, basic_config, group_infos = read_opc_config(cfg_msg, module)

    group_id_list = []
    group_id_lists = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    for gis in group_infos:
        group_id_list.append(gis['group_id'])
        gis = gis.pop('tags_num')
    group_new_list = list(set(group_id_lists).difference(set(group_id_list)))
    if group_new_list:
        group_new_list.sort()
        group_info = {'group_id': group_new_list[0], 'group_name': group_name,
                      'collect_cycle': collect_cycle, 'tags': []}

        group_infos.insert(group_new_list[0]-1, group_info)
        dict2 = {module+'.groups': group_infos}
        basic_config = {module+'.'+key: value for key,
                        value in basic_config.items()}
        data = {**basic_config, **dict2}

        res = {
            "module": "local",
            "data": data
        }
        with open(conf_path+module[:-1]+"_run_config.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(res, ensure_ascii=False,
                               sort_keys=False, indent=4))
        current_app.logger.debug(f'添加组{group_name}成功')
        return {'success': True, 'message': '添加组成功'}

    current_app.logger.debug(f'添加组{group_name}失败')
    return {'success': False, 'message': '当前不允许添加组,最大组数10'}


@cs.route('/alter_group', methods=['GET', 'POST'], endpoint='alter_group')
def alter_group():

    if request.method == 'POST':
        module = request.form.get('module')
        group_name = request.form.get('group_name')
        collect_cycle = int(request.form.get('collect_cycle'))
        group_id = int(request.form.get('group_id'))
        print(module, group_name, collect_cycle, group_id)
        cfg_msg = read_json(module)
        if module in modbus:
            tags, basic_config, group_infos = read_modbus_config(
                cfg_msg, module)
        else:
            tags, basic_config, group_infos = read_opc_config(cfg_msg, module)
        new_gis = {}
        for gis in group_infos:
            if gis['group_id'] == group_id:
                new_gis = {
                    'group_id': group_id,
                    'group_name': group_name,
                    'collect_cycle': collect_cycle,
                    'tags_num': gis['tags_num'],
                    'tags': gis['tags']
                }

        group_infos = [new_gis if gis['group_id'] ==
                       group_id else gis for gis in group_infos]
        for gis in group_infos:
            gis = gis.pop('tags_num')
        dict2 = {module+'.groups': group_infos}
        basic_config = {module+'.'+key: value for key,
                        value in basic_config.items()}
        data = {**basic_config, **dict2}

        res = {
            "module": "local",
            "data": data
        }
        with open(conf_path+"s_opcda_client_run_config.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(res, ensure_ascii=False,
                               sort_keys=False, indent=4))
        current_app.logger.debug(f'修改组{group_name}成功')
        return {'success': True, 'message': '修改组成功'}

    module = request.args.get('module')
    group_id = int(request.args.get('group_id'))

    cfg_msg = read_json(module)
    if module in modbus:
        tags, basic_config, group_infos = read_modbus_config(cfg_msg, module)
    else:
        tags, basic_config, group_infos = read_opc_config(cfg_msg, module)

    group_info = {}
    for gis in group_infos:
        if gis['group_id'] == group_id:
            group_info = gis
    if group_info:
        current_app.logger.debug(f'找到组{group_id}')
        return {'success': True, 'message': '找到组', 'group_info': group_info}
    current_app.logger.debug(f'找组{group_id}失败')
    return {'success': False, 'message': '没有找到组', 'group_info': group_info}


@cs.route('/delete_group', methods=['GET', 'POST'], endpoint='delete_group')
def delete_group():
    group_id = int(request.form.get('group_id', 1))
    module = request.form.get('module')
    cfg_msg = read_json(module)
    if module in modbus:
        tags, basic_config, group_infos = read_modbus_config(cfg_msg, module)
    else:
        tags, basic_config, group_infos = read_opc_config(cfg_msg, module)
    for index, gis in enumerate(group_infos):
        if gis['group_id'] == group_id:
            print(group_id)
            del group_infos[group_id-1]
        gis = gis.pop('tags_num')
    dict2 = {module+'.groups': group_infos}
    basic_config = {module+'.'+key: value for key,
                    value in basic_config.items()}
    data = {**basic_config, **dict2}

    res = {
        "module": "local",
        "data": data
    }
    with open(conf_path+"s_opcda_client_run_config.json", 'w', encoding='utf-8') as f:
        f.write(json.dumps(res, ensure_ascii=False,
                           sort_keys=False, indent=4))
    current_app.logger.debug(f'删除组:{group_id}成功')
    return {'success': True, 'message': '删除成功'}


@cs.route('/add_tag', methods=['GET', 'POST'], endpoint='add_tag')
def add_tag():
    group_id = int(request.form.get('group_id', 1))
    module = request.form.get('module')
    publish_tag_name = request.form.get('pub_name')
    source_tag_name = request.form.get('sub_name')
    data_type = request.form.get('data_type')
    # print(group_id,module,publish_tag_name,source_tag_name,data_type)
    cfg_msg = read_json(module)
    if module in modbus:
        tags, basic_config, group_infos = read_modbus_config(cfg_msg, module)
        data = search_modbus_tag(publish_tag_name, tags, [])
    else:
        tags, basic_config, group_infos = read_opc_config(cfg_msg, module)
        data = search_opc_tag(publish_tag_name, tags, [])
    if data:
        current_app.logger.debug(f'添加标签{publish_tag_name}失败，标签已经存在！')
        return {'success': False, 'message': '标签名已经存在'}
    for gis in group_infos:
        if gis['group_id'] == group_id:
            tag = {
                "tag_id": len(gis['tags']),
                "publish_tag_name": publish_tag_name,
                "source_tag_name": source_tag_name,
                "data_type": "ENUM_INT32"
            }
            gis['tags'].append(tag)
        gis = gis.pop('tags_num')

    dict2 = {module+'.groups': group_infos}
    basic_config = {module+'.'+key: value for key,
                    value in basic_config.items()}
    data = {**basic_config, **dict2}

    res = {
        "module": "local",
        "data": data
    }
    with open(conf_path+"s_opcda_client_run_config.json", 'w', encoding='utf-8') as f:
        f.write(json.dumps(res, ensure_ascii=False,
                           sort_keys=False, indent=4))
    current_app.logger.debug(f'添加标签{publish_tag_name}成功')
    return {'success': True, 'message': '添加标签点成功'}


@cs.route('/alter_tag', methods=['GET', 'POST'], endpoint='alter_tag')
def alter_tag():
    if request.method == 'POST':
        group_id = int(request.form.get('group_id', 1))
        tag_id = int(request.form.get('tag_id', 1))
        module = request.form.get('module')
        publish_tag_name = request.form.get('publish_tag_name')
        source_tag_name = request.form.get('source_tag_name')
        data_type = request.form.get('data_type')
        print(group_id, tag_id, module, publish_tag_name,
              source_tag_name, data_type)
        cfg_msg = read_json(module)
        if module in modbus:
            tags, basic_config, group_infos = read_modbus_config(
                cfg_msg, module)
            data = search_modbus_tag(publish_tag_name, tags, [])
        else:
            tags, basic_config, group_infos = read_opc_config(cfg_msg, module)
            data = search_opc_tag(publish_tag_name, tags, [])
        if data:
            current_app.logger.debug(f'修改标签{publish_tag_name}失败，标签已经存在！')
            return {'success': False, 'message': '标签名已经存在'}
        for gis in group_infos:
            if gis['group_id'] == group_id:
                for index, t in enumerate(gis['tags']):
                    if t['tag_id'] == tag_id:
                        new_tag = {
                            "tag_id": tag_id,
                            "publish_tag_name": publish_tag_name,
                            "source_tag_name": source_tag_name,
                            "data_type": "ENUM_INT32"
                        }

                        gis['tags'] = [new_tag if t['tag_id'] ==
                                       tag_id else t for t in gis['tags']]
        for gis in group_infos:
            gis = gis.pop('tags_num')
        dict2 = {module+'.groups': group_infos}
        basic_config = {module+'.'+key: value for key,
                        value in basic_config.items()}
        data = {**basic_config, **dict2}

        res = {
            "module": "local",
            "data": data
        }
        with open(conf_path+"s_opcda_client_run_config.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(res, ensure_ascii=False,
                               sort_keys=False, indent=4))
        current_app.logger.debug(f'修改标签{publish_tag_name}成功')
        return {'success': True, 'message': '修改标签点成功'}

    module = request.args.get('module')
    group_id = int(request.args.get('group_id', 1))
    publish_tag_name = request.args.get('publish_tag_name')
    cfg_msg = read_json(module)
    if module in modbus:
        tags, basic_config, group_infos = read_modbus_config(cfg_msg, module)
        data = search_modbus_tag(publish_tag_name, tags, [])
    else:
        tags, basic_config, group_infos = read_opc_config(cfg_msg, module)
        data = search_opc_tag(publish_tag_name, tags, [])
    if not data:
        current_app.logger.debug(f'修改标签{publish_tag_name}失败，标签不存在！')
        return {'success': False, 'message': '标签名不存在'}
    for gis in group_infos:
        if gis['group_id'] == group_id:
            for index, t in enumerate(gis['tags']):
                if t['publish_tag_name'] == publish_tag_name:
                    tag = t
                    break
    current_app.logger.debug(f'请求修改标签{publish_tag_name}成功')
    return {'success': True, 'message': '请求修改标签点成功', 'tag': publish_tag_name}


@cs.route('/delete_tag', methods=['GET', 'POST'], endpoint='delete_tag')
def delete_tag():
    group_id = int(request.args.get('group_id', 1))
    module = request.args.get('module')
    publish_tag_name = request.args.get('publish_tag_name')

    # print(group_id,module,publish_tag_name)
    cfg_msg = read_json(module)
    if module in modbus:
        tags, basic_config, group_infos = read_modbus_config(cfg_msg, module)
        data = search_modbus_tag(publish_tag_name, tags, [])
    else:
        tags, basic_config, group_infos = read_opc_config(cfg_msg, module)
        data = search_opc_tag(publish_tag_name, tags, [])
    if not data:
        current_app.logger.debug(f'标签{publish_tag_name}不存在')
        return {'success': False, 'message': '标签名不存在'}
    for gis in group_infos:
        if gis['group_id'] == group_id:
            for index, t in enumerate(gis['tags']):
                if t['publish_tag_name'] == publish_tag_name:
                    print(t)
                    gis['tags'].pop(index)
                    break
        gis = gis.pop('tags_num')

    dict2 = {module+'.groups': group_infos}
    basic_config = {module+'.'+key: value for key,
                    value in basic_config.items()}
    data = {**basic_config, **dict2}
    res = {
        "module": "local",
        "data": data
    }
    with open(conf_path+"s_opcda_client_run_config.json", 'w', encoding='utf-8') as f:
        f.write(json.dumps(res, ensure_ascii=False,
                           sort_keys=False, indent=4))
    current_app.logger.debug(f'删除标签{publish_tag_name}成功')
    return {'success': True, 'message': '删除标签点成功', 'tag_name': publish_tag_name}


"""
##################################### config_setting ###############################

"""


@cs.route('/opc', methods=['GET', 'POST'], endpoint='opc')
def da_client():
    opc_ae_form = OpcForm()
    opc_da_form = OpcdaForm()
    return render_template('opc/da_ae_client.html', opc_ae_form=opc_ae_form, opc_da_form=opc_da_form)


@cs.route('/load_opc_se', methods=['GET', 'POST'], endpoint='load_opc_se')
@login_required
def load_opc_sev():
    if request.method == 'POST':
        module = request.form['module']
        enAutoTag = int(request.form['enAutoTag'])
        isDataConvert = int(request.form['isDataConvert'])
        tag_list = []
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

                for name in names:
                    st = wb.sheet_by_name(name)
                    nrows = st.nrows
                    tags_list = st.col_values(0, start_rowx=1, end_rowx=nrows)
                    for m in range(len(tags_list)):
                        publish_tag_name = tags_list[m]
                        tag_value = [publish_tag_name, write_able, data_type]
                        X = dict(zip(tag_key, tag_value))
                        tag_list.append(X)

        basic_config = {module+'.enAutoTag': enAutoTag,
                        module+'.isDataConvert': isDataConvert}
        tags = {module+'.tags': tag_list}

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

    return render_template("opc/opc_se_index.html", opc_da_server='bg-info')


@ cs.route('/load_opc_da', methods=['GET', 'POST'], endpoint='load_opc_da')
@login_required
def load_opc_da():
    if request.method == 'POST':
        module = request.form['module']
        main_server_ip = request.form['main_server_ip']
        main_server_prgid = request.form['main_server_prgid']
        main_server_clsid = request.form['main_server_clsid']
        main_server_domain = request.form['main_server_domain']
        main_server_user = request.form['main_server_user']
        main_server_password = request.form['main_server_password']
        bak_server_ip = request.form['bak_server_ip']
        bak_server_prgid = request.form['bak_server_prgid']
        bak_server_clsid = request.form['bak_server_clsid']
        bak_server_domain = request.form['bak_server_domain']
        bak_server_user = request.form['bak_server_user']
        bak_server_password = request.form['bak_server_password']

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
                group_id = int(name.split('-', 1)
                               [0][5:len(name.split('-', 1)[0])])
                group_name = name.split('-', 1)[0]
                collect_cycle = int(name.split('-', 1)[1])
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
        tags, basic_config, _ = read_modbus_config(cfg_msg, module)
        set_config(res, module)
        return render_template("opc/opc_show.html", basic_config=dict1)
    return render_template("opc/opc_da_index.html", opc_da_client='bg-danger')


@ cs.route('/load_opc_ae', methods=['GET', 'POST'], endpoint='load_opc_ae')
@login_required
def load_opc_ae():
    if request.method == 'POST':
        module = request.form['module']
        main_server_ip = request.form['main_server_ip']
        main_server_prgid = request.form['main_server_prgid']
        main_server_clsid = request.form['main_server_clsid']
        main_server_domain = request.form['main_server_domain']
        main_server_user = request.form['main_server_user']
        main_server_password = request.form['main_server_password']
        bak_server_ip = request.form['bak_server_ip']
        bak_server_prgid = request.form['bak_server_prgid']
        bak_server_clsid = request.form['bak_server_clsid']
        bak_server_domain = request.form['bak_server_domain']
        bak_server_user = request.form['bak_server_user']
        bak_server_password = request.form['bak_server_password']

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
        tags, basic_config, _ = read_opc_config(cfg_msg, module)
        set_config(res, module)
        return render_template("opc/opc_show.html", basic_config=dict1)
    return render_template("opc/opc_ae_index.html", opc_ae_client='bg-warning')


@cs.route('/load_modbus', methods=['GET', 'POST'], endpoint='load_modbus')
@login_required
def load_modbus():
    if request.method == 'POST':
        module = request.form.get('module', 'modbus1')
        dev_id = request.form.get('id', 1)
        Coll_Type = request.form.get('type', 'RTU')
        host = request.form.get('ip', '172.16.2.100')
        port = request.form.get('port', 502)
        serial = request.form.get('com', 'com1')
        baud = request.form.get('baud', 9600)
        data_bit = request.form.get('data_bit', 8)
        stop_bit = request.form.get('stop_bit', 1)
        parity = request.form.get('parity', None)

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
        if f and allowed_file(f.filename):
            f.save(conf_path+secure_filename(f.filename))
            names = []
            xl = list(p.rglob('modbus.xlsx'))
            for T in xl:
                wb = xlrd.open_workbook(T)
                names = wb.sheet_names()
            data_list = []      # 站 号
            data_dict = {"slave_id": 0, "block": []}
            block_dict = {'fun_code': 0, 'tags': []}
            wb = None
            for name in names:
                st = wb.sheet_by_name(name)
                nrows = st.nrows
                ncols = st.ncols
                d_type_1 = ['INT16', 'UINT16']
                d_type_2 = ['INT32', 'UINT32', 'FLOAT', 'DOUBLE']

                tags = []
                block_list = []   # 功能码
                slave_id = []
                fun_code = []
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

                if not data_dict['slave_id'] == int(slave_id[0]):
                    data_dict = {"slave_id": int(
                        slave_id[0]), "block": block_list}
                    data_list.append(data_dict)

                for index, dt in enumerate(data_list):
                    if dt['slave_id'] == int(slave_id[0]):
                        block_dict = {'fun_code': int(
                            fun_code[0]), 'tags': tags}
                        dt['block'].append(block_dict)

            dict2 = {module+'.data': data_list}
        data = {**dict1, **dict2}
        res = {
            "module": "local",
            "data": data
        }
        with open(conf_path+"modbus_run_config.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(res, ensure_ascii=False,
                               sort_keys=False, indent=4))
        cfg_msg = read_json(module)
        tags, basic_config, _ = read_modbus_config(cfg_msg, module)
        set_config(res, module)
        return render_template('opc/opc_show.html', basic_config=basic_config)
    return render_template('modbus/modbus_index.html', modbus_slave='bg-primary')


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
        tags, basic_config, _ = read_opc_config(cfg_msg, module)
        current_app.logger.debug(f'开始编辑{module}基础配置')
    else:
        tags, basic_config, _ = read_modbus_config(cfg_msg, module)
        current_app.logger.debug(f'开始编辑{module}基础配置')
    return {'basic_config': basic_config}


@ cs.route('/config_review', methods=['GET', 'POST'], endpoint='config_review')
@login_required
def config_review():
    if request.method == 'POST':
        module = request.form['module']
        cfg_msg = read_json(module)
        if module in opc:
            tags, basic_config, _ = read_opc_config(cfg_msg, module)
            current_app.logger.info(f'查看{module}基础配置')
        else:
            tags, basic_config, _ = read_modbus_config(cfg_msg, module)
            current_app.logger.debug(f'查看{module}基础配置')
        return {'basic_config': basic_config}

    module = 's_opcda_client1'
    cfg_msg = read_json(module)
    if module in opc:
        tags, basic_config, _ = read_opc_config(cfg_msg, module)
    else:
        tags, basic_config, _ = read_modbus_config(cfg_msg, module)
    return render_template('opc/opc_show.html', basic_config=basic_config, config_review='bg-success')


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
            tags, basic_config, _ = read_modbus_config(cfg_msg, module)
            current_app.logger.debug(f'查看{module}位号配置')
        return {'tags': tags}

    # module1 = request.args.get('module')
    module = 's_opcda_client1'
    cfg_msg = read_json(module)
    if module in opc:
        tags, basic_config, _ = read_opc_config(cfg_msg, module)
    else:
        tags, basic_config, _ = read_modbus_config(cfg_msg, module)
    return render_template('opc/opc_tags.html', tags=tags, tags_review='bg-danger')


@ cs.route('/get_config', methods=['GET', 'POST'], endpoint='get_config')
def get_config():
    if request.method == 'POST':
        res_msg = {}
        module = request.form['module']
        json_data = {'module': module}
        res, stu = call_s_config(URL['getconfig_url'], json_data)
        if stu:
            res_msg = decode_config(res, module)

            user_name = g.user.username
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
def log():
    logs_list = []
    if request.method == 'POST':
        log_level = request.form.get('log_level', 'ALL')
        log_day = request.form.get('log_day', time.strftime('%Y-%m-%d'))
        log_day_start = log_day+' ' + \
            request.form.get('log_day_start', '00:00:00')
        log_day_end = log_day+' '+request.form.get("log_day_end", "23:59:59")
        pages = int(request.form.get('pages', 10))
        page = int(request.form.get('page', 1))
        key = request.form.get('key')
        log_name = log_path+'\\'+'{}.log'.format(log_day)
        if not all((log_day, log_day_start, log_day_end)):
            return {'paginate': {}, 'msg': f'请输入查询日期和时间'}
        try:
            with open(log_name, 'r', encoding='utf-8') as lg:
                logs = lg.read().splitlines()
        except Exception as e:
            return {'paginate': {}, 'msg': f'OOOPS..[{log_day}]没有日志,被外星人偷走了？？'}
        text = linecache.getline(log_name, 2)[1:-1]
        logs_list = check_day_log(
            log_day_start, log_day_end, logs, log_level, key)
        if logs_list:
            pga = paginate(logs_list, page, pages)
            return {"paginate": pga, 'msg': f'查询到条日志'}
        else:
            return {'paginate': {}, 'msg': f'查询到0条日志'}

    else:
        pages = int(request.args.get('pages', 14))
        page = int(request.args.get('page', 1))
        with open(log_path+'\\'+'{}.log'.format(time.strftime('%Y-%m-%d')), 'r', encoding='utf-8') as lg:
            logs = lg.read().splitlines()
        for l in logs:
            logs_list.append(l.rsplit('  '))
        pga = paginate(logs_list, page, pages)
        return render_template('log/log.html', paginate=pga, log='bg-info')


ec = EventClient()
sc = SensorClient()

@cs.route("/show_sensor", methods=['GET', 'POST'], endpoint='show_sensor')
def show_sensor():
    tags = []
    if request.method == 'POST':
        page = int(request.form.get('page', 1))
        pages = int(request.form.get('pages', 3))
    else:
        page = int(request.args.get('page', 1))
        pages = int(request.args.get('pages', 3))

    for data in sc.sensor_list:
        tags.append(sensor2dict(data))
    pga = paginate(tags, page, pages)
    if request.method == 'POST':
        return {'paginate': pga}
    return render_template('opc/show_sensor.html', paginate=pga, show_sensor='bg-warning')


@cs.route("/show_alarm", methods=['GET', 'POST'], endpoint='show_alarm')
def show_alarm():
    tags = []
    if request.method == 'POST':
        page = int(request.form.get('page', 1))
        pages = int(request.form.get('pages', 3))
    else:
        page = int(request.args.get('page', 1))
        pages = int(request.args.get('pages', 3))

    for data in ec.event_list:
        tags.append(event2dict(data))
    pga = paginate(tags, page, pages)
    if request.method == 'POST':
        return {'paginate': pga}
    return render_template('opc/show_alarm.html', paginate=pga, show_alarm='bg-warning')


def search_process(key, source, pc_list):
    if '*' in key:
        for s in source:
            if key[1:] in s['tag']:
                pc_list.append(s)
    else:
        for s in source:
            if s['tag'] == key:
                pc_list.append(s)

    return pc_list


@cs.route("/control", methods=['GET', 'POST'], endpoint='control')
def control():
    tags = []
    if request.method == 'POST':
        page = int(request.form.get('page', 1))
        pages = int(request.form.get('pages', 10))
        key = request.form.get('key')

    else:
        page = int(request.args.get('page', 1))
        pages = int(request.args.get('pages', 5))
        key = request.args.get('key', '*pid')

    for data in sc.sensor_list:
        tags.append(sensor2dict(data))

    pc_list = search_process(key, tags, [])
    pga = paginate(pc_list, page, pages)
    if request.method == 'POST':
        return {'paginate': pga}
    return render_template('opc/control.html', paginate=pga, control='bg-danger')


@cs.route("/restart", methods=['GET', 'POST'], endpoint='restart')
def restart():
    pid = request.form.get('pid')
    kill_process(pid)
    return {'success': True, 'msg': '重启成功'}

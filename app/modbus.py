import xlrd
import json
import time
import datetime
import re
from flask import redirect, url_for
from flask import request, render_template, Blueprint, current_app, session
from werkzeug.utils import secure_filename
from .settings import Config
from flask import g
from app.utils import paginate
from app.opc import login_required

conf_path = Config.conf_path
log_path = Config.log_path
p = Config.p


mt = Blueprint('mt', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'xls', 'xlsx'}


def search_modbus_tag(key, source, tag_list):
    try:
        if key[-1] == "*":
            for s in source:
                m = re.search('('+key[:-1]+')?', s['tag'])
                n = re.search('('+key[:-1]+')?', str(s['start']))
                aa = m.group(0)
                bb = n.group(0)
                if aa or bb:
                    tag_list.append(s)
        else:
            for s in source:
                if s['tag'] == key or str(s['start']) == key:
                    tag_list.append(s)

        return tag_list
    except Exception as e:
        print(str(e))
        return []



def read_json():
    json_name = conf_path+'modbus_run_config.json'
    cfg_msg = {}
    try:
        with open(json_name, 'r', encoding='utf-8') as f:
            cfg_msg = json.loads(f.read())
        return cfg_msg
    except Exception as e:
        print(str(e))
        return cfg_msg


def read_modbus_config(cfg_msg):
    basic_config = {}
    data_list = []
    group_infos = []
    if cfg_msg:
        try:
            dev_id = cfg_msg['dev_id']
            Coll_Type = cfg_msg['Coll_Type']
            TCP = cfg_msg['TCP']
            RTU = cfg_msg['RTU']

            basic_config = {
                'dev_id': dev_id,
                'Coll_Type': Coll_Type,
                'TCP': {
                    'host': TCP['host'],
                    'port': TCP['port']},
                'RTU': {
                    'serial': RTU['serial'],
                    'baud': RTU['baud'],
                    'data_bit': RTU['data_bit'],
                    'stop_bit': RTU['stop_bit'],
                    'parity': RTU['parity'], }
            }
            i = 1
            for data in cfg_msg['data']:
                slave_id = data['slave_id']
                datas = {'slave_id': slave_id, 'block': data['block']}
                data_list.append(datas)
                for b_d in data['block']:
                    fun_code = b_d['fun_code']
                    tags = b_d['tags']
                    group_info = {'id': i, 'slave_id': slave_id,
                                  'fun_code': fun_code, 'tag_num': len(tags), 'tags': tags}
                    group_infos.append(group_info)
                    i += 1
            return basic_config, data_list, group_infos
        except Exception as e:
            print(str(e), '------error in read modbus conf----------')
            return basic_config, data_list, group_infos
    else:
        return basic_config, data_list, group_infos,


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




@mt.route('/m_tag_search', methods=['GET', 'POST'], endpoint='m_tag_search')
def m_tag_search():
    """
    查找
    """
    key = request.args.get('key')  # 标签名
    slave_id = int(request.args.get('slave_id', 1))
    fun_code = int(request.args.get('fun_code', 3))
    pages = int(request.args.get('pages', 10))
    page = int(request.args.get('page', 1))
    cfg_msg = read_json()
    search_tag_list = []
    basic_config, data, group_infos = read_modbus_config(cfg_msg)
    for gis in group_infos:
        if gis['slave_id'] == slave_id and gis['fun_code'] == fun_code:
            tags = gis['tags']
            search_tag_list = search_modbus_tag(key, tags, [])
    pga = paginate(search_tag_list, page, pages)

    current_app.logger.debug(f'查询位号:%s' % (key))
    return {"paginate": pga, 'group_infos': group_infos}

# 未实现
@mt.route('/m_add_group', methods=['GET', 'POST'], endpoint='m_add_group')
def m_add_group():
    slave_id = request.form.get('slave_id')
    fun_code = request.form.get('fun_code')
    print(slave_id, fun_code)
    cfg_msg = read_json()
    basic_config, data, group_infos = read_modbus_config(cfg_msg)
    for gi in group_infos:
        print(gi['group_id'])
    group_info = {'group_id': 1, 'slave_id': slave_id, 'fun_code': fun_code,
                  'collect_cycle': 5, 'tags_num': 0, 'tags': []}

    group_infos.insert(1, group_info)
    dict2 = {'groups': group_infos}
    basic_config = {''+key: value for key,
                    value in basic_config.items()}
    data = {**basic_config, **dict2}

    res = {
        "module": "local",
        "data": data
    }
    with open(conf_path+"modbus_run_config.json", 'w', encoding='utf-8') as f:
        f.write(json.dumps(res, ensure_ascii=False,
                           sort_keys=False, indent=4))
    current_app.logger.debug(f'添加组成功')
    return {'success': True, 'message': '添加组成功'}


# 未实现
@mt.route('/m_alter_group', methods=['GET', 'POST'], endpoint='m_alter_group')
def m_alter_group():
    if request.method == 'POST':
        id = int(request.form.get('id'))
        slave_id = int(request.form.get('slave_id'))
        fun_code = int(request.form.get('fun_code'))
        print(id, slave_id, fun_code)
        cfg_msg = read_json()
        basic_config, data_list, group_infos = read_modbus_config(cfg_msg)
        old_slave_id, old_fun_code = 0, 0
        for gis in group_infos:
            if gis['id'] == id:
                old_slave_id, old_fun_code = gis['slave_id'], gis['fun_code']
        print(old_slave_id, old_fun_code)
        if old_slave_id != slave_id and old_fun_code == fun_code:
            for d_l in data_list:
                if d_l['slave_id'] == old_slave_id:
                    for b in d_l['block']:
                        if b['fun_code'] == old_fun_code:
                            new_data_list = {
                                'slave_id': slave_id,
                                'block': [{'fun_code': fun_code, 'tags': b['tags']}],
                            }
                            data_list = [new_data_list if d_l['slave_id']
                                         == old_slave_id else d_l for d_l in data_list]
        elif old_slave_id == slave_id and old_fun_code != fun_code:
            for d_l in data_list:
                if d_l['slave_id'] == old_slave_id:
                    for b in d_l['block']:
                        if b['fun_code'] == old_fun_code:
                            b['fun_code'] = fun_code
        else:
            for d_l in data_list:
                if d_l['slave_id'] == old_slave_id:
                    for b in d_l['block']:
                        if b['fun_code'] == old_fun_code:
                            new_data_list = {
                                'slave_id': slave_id,
                                'block': [{'fun_code': fun_code, 'tags': b['tags']}],
                            }
                            data_list = [new_data_list if d_l['slave_id']
                                         == old_slave_id else d_l for d_l in data_list]
        dict2 = {'data': data_list}
        res = {**basic_config, **dict2}

        with open(conf_path+"modbus_run_config.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(res, ensure_ascii=False,
                               sort_keys=False, indent=4))
        current_app.logger.debug(f'修改组{id}成功')
        return {'success': True, 'message': '修改组成功'}

    id = int(request.args.get('id'))
    slave_id = int(request.args.get('slave_id'))
    fun_code = int(request.args.get('fun_code'))

    cfg_msg = read_json()

    basic_config, data, group_infos = read_modbus_config(cfg_msg)

    group_info = {}
    for gis in group_infos:
        if gis['slave_id'] == slave_id and gis['fun_code'] == fun_code:
            group_info = gis

    if group_info:
        current_app.logger.debug(f'找到组{id}')
        return {'success': True, 'message': '找到要修改的组', 'group_info': group_info}
    current_app.logger.debug(f'找组{id}失败')
    return {'success': False, 'message': '没有找到要修改的组', 'group_info': group_info}


@mt.route('/m_delete_group', methods=['GET', 'POST'], endpoint='m_delete_group')
def m_delete_group():
    id = int(request.form.get('id', 1))
    cfg_msg = read_json()
    basic_config, data_list, group_infos = read_modbus_config(cfg_msg)
    slave_id,fun_code=0,0
    for gis in group_infos:
        if gis['id'] == id:
            slave_id, fun_code = gis['slave_id'], gis['fun_code']
    print(slave_id, fun_code)
    for d_l in data_list:
        if d_l['slave_id'] == slave_id:
            for index, b in enumerate(d_l['block']):
                if b['fun_code'] == fun_code:
                    del d_l['block'][index]

    dict2 = {'data': data_list}
    res = {**basic_config, **dict2}

    with open(conf_path+"modbus_run_config.json", 'w', encoding='utf-8') as f:
        f.write(json.dumps(res, ensure_ascii=False,
                           sort_keys=False, indent=4))
    current_app.logger.debug(f'删除组:{id}成功')
    return {'success': True, 'message': '删除成功'}


@mt.route('/m_add_tag', methods=['GET', 'POST'], endpoint='m_add_tag')
def m_add_tag():
    slave_id = int(request.form.get('slave_id', 1))
    fun_code = int(request.form.get('fun_code', 1))
    tag_name = request.form.get('tag')
    start = request.form.get('start')
    register_number = request.form.get('register_number')
    data_type = request.form.get('data_type')
    data_format = request.form.get('data_format')
    desc = request.form.get('desc')
    print(slave_id, fun_code, tag_name, start,
          register_number, data_type, data_format, desc)
    cfg_msg = read_json()

    basic_config, data, group_infos = read_modbus_config(cfg_msg)
    tags=[]
    for gis in group_infos:
        if gis['slave_id'] == slave_id and gis['fun_code'] == fun_code:
            tags = gis['tags']
    t = search_modbus_tag(tag_name, tags, [])
    s = search_modbus_tag(start, tags, [])

    if t or s:
        current_app.logger.debug(f'添加标签{tag_name}失败，标签名或地址已经存在！')
        return {'success': False, 'message': '标签名或地址已经存在'}
    for d in data:
        if d['slave_id'] == slave_id:
            for d_b in d['block']:
                if d_b['fun_code'] == fun_code:
                    tag = {
                        "tag": tag_name,
                        "start": start,
                        "register_number": register_number,
                        "data_type": data_type,
                        "data_format": data_format,
                        "desc": desc
                    }
                    d_b['tags'].append(tag)

    dict2 = {'data': data}
    res = {**basic_config, **dict2}

    with open(conf_path+"modbus_run_config.json", 'w', encoding='utf-8') as f:
        f.write(json.dumps(res, ensure_ascii=False,
                           sort_keys=False, indent=4))
    current_app.logger.debug(f'添加标签{tag_name}成功')
    return {'success': True, 'message': '添加标签点成功'}


@mt.route('/m_alter_tag', methods=['GET', 'POST'], endpoint='m_alter_tag')
def m_alter_tag():
    if request.method == 'POST':
        slave_id = int(request.form.get('slave_id', 1))
        fun_code = int(request.form.get('fun_code', 3))
        tag_name = request.form.get('tag')
        start = request.form.get('start')
        register_number = request.form.get('register_number')
        data_type = request.form.get('data_type')
        data_format = request.form.get('data_format')
        desc = request.form.get('desc')
        # print(slave_id,fun_code,tag,start,register_number,data_type,data_format,desc)
        cfg_msg = read_json()

        basic_config, data, group_infos = read_modbus_config(cfg_msg)
        tags=[]
        for gis in group_infos:
            if gis['slave_id'] == slave_id and gis['fun_code'] == fun_code:
                tags = gis['tags']
        t = search_modbus_tag(tag_name, tags, [])
        s = search_modbus_tag(start, tags, [])

        if not t:
            current_app.logger.debug(f'修改标签{tag_name}失败，标签名不存在！')
            return {'success': False, 'message': '失败，标签名或地址不存在！'}
        alter_tag = {
            "tag": tag_name,
            "start": start,
            "register_number": register_number,
            "data_type": data_type,
            "data_format": data_format,
            "desc": desc
        }
        for d in data:
            if d['slave_id'] == slave_id:
                for d_b in d['block']:
                    if d_b['fun_code'] == fun_code:
                        for index, t in enumerate(d_b['tags']):

                            d_b['tags'] = [alter_tag if t['tag'] ==
                                           tag_name else t for t in d_b['tags']]

        dict2 = {'data': data}
        res = {**basic_config, **dict2}

        with open(conf_path+"modbus_run_config.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(res, ensure_ascii=False,
                               sort_keys=False, indent=4))
        current_app.logger.debug(f'修改标签{tag_name}成功')
        return {'success': True, 'message': '修改标签点成功'}

    slave_id = int(request.args.get('slave_id', 1))
    fun_code = int(request.args.get('fun_code', 1))
    tag_name = request.args.get('tag_name')

    print(slave_id, fun_code, tag_name)
    cfg_msg = read_json()
    search_tag_list = []
    basic_config, data, group_infos = read_modbus_config(cfg_msg)
    for gis in group_infos:
        if gis['slave_id'] == slave_id and gis['fun_code'] == fun_code:
            tags = gis['tags']
            search_tag_list = search_modbus_tag(tag_name, tags, [])
    current_app.logger.debug(f'请求修改标签{tag_name}成功')
    return {'success': True, 'message': '请求修改标签点成功', 'tag': search_tag_list[0]}


@mt.route('/m_delete_tag', methods=['GET', 'POST'], endpoint='m_delete_tag')
def m_delete_tag():
    slave_id = int(request.args.get('slave_id', 1))
    fun_code = int(request.args.get('fun_code', 3))
    tag_name = request.args.get('tag_name')

    print(slave_id, fun_code, tag_name)
    cfg_msg = read_json()
    basic_config, data_list, group_infos = read_modbus_config(cfg_msg)
    search_tag_list=[]
    for gis in group_infos:
        if gis['slave_id'] == slave_id and gis['fun_code'] == fun_code:
            tags = gis['tags']
            search_tag_list = search_modbus_tag(tag_name, tags, [])
    if not search_tag_list:
        current_app.logger.debug(f'标签{tag_name}不存在')
        return {'success': False, 'message': '标签名不存在'}

    for d in data_list:
        if d['slave_id'] == slave_id:
            for d_b in d['block']:
                if d_b['fun_code'] == fun_code:
                    for index, t in enumerate(d_b['tags']):
                        if t['tag'] == tag_name:
                            del d_b['tags'][index]
    dict2 = {'data': data_list}
    res = {**basic_config, **dict2}
    with open(conf_path+"modbus_run_config.json", 'w', encoding='utf-8') as f:
        f.write(json.dumps(res, ensure_ascii=False,
                           sort_keys=False, indent=4))
    current_app.logger.debug(f'删除标签{tag_name}成功')
    return {'success': True, 'message': '删除标签点成功', 'tag_name': tag_name}


@mt.route('/modbus', methods=['GET', 'POST'], endpoint='modbus')
@login_required
def load_modbus():
    if request.method == 'POST':
        dev_id = request.form.get('dev_id', 1)
        Coll_Type = request.form.get('Coll_Type', 'RTU')
        host = request.form.get('ip', '172.16.2.100')
        port = request.form.get('port', 502)
        serial = request.form.get('com', 'com1')
        baud = request.form.get('baud', 9600)
        data_bit = request.form.get('data_bit', 8)
        stop_bit = request.form.get('stop_bit', 1)
        parity = request.form.get('parity', None)

        dict1 = {
            'dev_id': dev_id,
            'Coll_Type': Coll_Type,
            'TCP': {'host': host,
                    'port': port},
            'RTU': {'serial': serial,
                    'baud': baud,
                    'data_bit': data_bit,
                    'stop_bit': stop_bit,
                    'parity': parity}
        }
        dict2 = {}
        data_list=[]
        f = request.files['file']
        if f and allowed_file(f.filename):
            f.save(conf_path+secure_filename(f.filename))

            xl = list(p.rglob('modbus.xlsx'))
            names=[]
            wb=[]
            for T in xl:
                wb = xlrd.open_workbook(T)
                names = wb.sheet_names()
            data_list = []      # 站 号
            data_dict = {"slave_id": 0, "block": []}
            block_dict = {'fun_code': 0, 'tags': []}
            for name in names:
                st = wb.sheet_by_name(name)
                nrows = st.nrows
                ncols = st.ncols
                d_type_1 = ['INT16', 'UINT16']
                d_type_2 = ['INT32', 'UINT32', 'FLOAT', 'DOUBLE']

                tags = []
                block_list = []   # 功能码
                slave_id=[]
                fun_code=[]
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

        dict2 = {'data': data_list}
        res = {**dict1, **dict2}
        with open(conf_path+"modbus_run_config.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(res, ensure_ascii=False,
                               sort_keys=False, indent=4))
        current_app.logger.debug('保存配置成功！')
        return redirect(url_for('mt.show_modbus_page'))
    return render_template('modbus/modbus_index.html', modbus='bg-info')


@mt.route('/show_modbus_page', methods=['GET', 'POST'], endpoint='show_modbus_page')
@login_required
def show_modbus_page():
    group_infos = []
    if request.method == 'POST':
        id = int(request.form.get('id', 1))-1
        pages = int(request.form.get('pages', 10))
        page = int(request.form.get('page', 1))
        cfg_msg = read_json()
        basic_config, data, group_infos = read_modbus_config(cfg_msg)
        config = {
            'dev_id': basic_config['dev_id'],
            'Coll_Type':  basic_config['Coll_Type'],

            'host': basic_config['TCP']['host'],
            'port': basic_config['TCP']['port'],

            'serial': basic_config['RTU']['serial'],
            'baud': basic_config['RTU']['baud'],
            'data_bit': basic_config['RTU']['data_bit'],
            'stop_bit': basic_config['RTU']['stop_bit'],
            'parity': basic_config['RTU']['parity']
        }
        if group_infos:
            pga = paginate(group_infos[id]['tags'], page, pages)
            return {"paginate": pga, 'group_infos': group_infos, 'basic_config': config}
        return {"paginate": [], 'group_infos': []}

    pages = int(request.args.get('pages', 10))
    page = int(request.args.get('page', 1))
    cfg_msg = read_json()
    basic_config, data, group_infos = read_modbus_config(cfg_msg)
    pga = paginate(group_infos, page, pages)
    config = {
        'dev_id': basic_config['dev_id'],
        'Coll_Type':  basic_config['Coll_Type'],

        'host': basic_config['TCP']['host'],
        'port': basic_config['TCP']['port'],

        'serial': basic_config['RTU']['serial'],
        'baud': basic_config['RTU']['baud'],
        'data_bit': basic_config['RTU']['data_bit'],
        'stop_bit': basic_config['RTU']['stop_bit'],
        'parity': basic_config['RTU']['parity']
    }
    print(pga['total'],pga['pages'])
    return render_template('modbus/modbus_show.html', paginate=pga, group_infos=group_infos, basic_config=config, modbus='bg-info')


@ mt.route('/log', methods=['GET', 'POST'], endpoint='log')
@login_required
def log():
    logs_list = []
    if request.method == 'POST':
        logs_list = []
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
        logs_list = check_day_log(
            log_day_start, log_day_end, logs, log_level, key)
        if logs_list:
            pga = paginate(logs_list, page, pages)

            return {"paginate": {}, 'msg': f'查询到{pga.total}条日志'}
        else:
            return {'paginate': {}, 'msg': f'查询到0条日志'}
    else:
        pages = int(request.args.get('pages', 5))
        page = int(request.args.get('page', 1))
        with open(log_path+'\\'+'{}.log'.format(time.strftime('%Y-%m-%d')), 'r', encoding='utf-8') as lg:
            logs = lg.read().splitlines()
        for l in logs:
            logs_list.append(l.rsplit('  '))
        pga = paginate(logs_list, page, pages)
        return render_template('log/log.html', paginate=pga, log='bg-info')

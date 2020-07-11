#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: hyy
@file: pyecharts
@time: 2020/06/27
@desc:

"""
import random
from flask import render_template, Blueprint
from flask import jsonify
from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.charts import Line
from pyecharts.charts import Pie
from pyecharts.charts import Gauge


ct = Blueprint("ct", __name__)

@ct.route("/gauge", methods=['GET'], endpoint='gauge')
def gauge():
    return render_template("charts/gauge.html")


@ct.route("/update_gauge_cpu", methods=['GET'], endpoint='update_gauge_cpu')
def update_gauge_cpu():
    return jsonify({"name": 'CPU', "value": random.randrange(1, 100)})

@ct.route("/update_gauge_memory", methods=['GET'], endpoint='update_gauge_memory')
def update_gauge_memory():
    return jsonify({"name": 'MEMORY', "value": random.randrange(1, 100)})
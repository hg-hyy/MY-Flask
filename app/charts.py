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


ct = Blueprint("ct", __name__)


def line_base() -> Line:
    line = (
        Line()
        .add_xaxis(["{}".format(i) for i in range(10)])
        .add_yaxis(
            series_name="",
            y_axis=[random.randrange(50, 80) for _ in range(10)],
            is_smooth=True,
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="动态数据"),
            xaxis_opts=opts.AxisOpts(type_="value"),
            yaxis_opts=opts.AxisOpts(type_="value"),
        )
    )
    return line



@ct.route("/line",methods=['GET'], endpoint='line')
def line():
    return render_template("charts/line_chart.html")


@ct.route("/get_line_chart", methods=['GET'], endpoint='get_line_chart')
def get_line_chart():
    c = line_base()
    return c.dump_options_with_quotes()


idx = 9
@ct.route("/update_line_data", methods=['GET'], endpoint='update_line_data')
def update_line_data():
    global idx
    idx = idx + 1
    return jsonify({"name": idx, "value": random.randrange(50, 80)})



def pie_base() -> Pie:
    c = (
        Pie()
        .add_xaxis(["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"])
        .add_yaxis("商家A", [random.randint(10, 100) for _ in range(6)])
        .add_yaxis("商家B", [random.randint(10, 100) for _ in range(6)])
        .set_global_opts(title_opts=opts.TitleOpts(title="", subtitle=""))
    )
    return c

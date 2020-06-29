#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: hyy
@file: tools
@time: 2020/06/27
@desc:

"""
from math import ceil
import datetime
import os
import time
import xlrd
import json
import re
import functools
import linecache
import requests

from pathlib import Path
from flask import request, render_template, Blueprint, session, url_for
from flask import Markup, make_response, jsonify, flash, current_app, redirect, g


def log_class(level):
    """自定义过滤器"""
    if level == '[DEBUG]':
        return "table-warning"
    elif level == '[INFO ]':
        return "table-info"
    elif level == '[ERROR]':
        return "table-danger"
    else:
        return "table-info"

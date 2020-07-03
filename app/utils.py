#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: hyy
@file: tools
@time: 2020/06/27
@desc:

"""
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: hyy
@file: tools
@time: 2020/06/27
@desc:

"""
from math import ceil


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


class Pagination(object):

    def __init__(self, page, per_page, total, items):
        #: the unlimited query object that was used to create this
        #: pagination object.
        #: the current page number (1 indexed)
        self.page = page
        #: the number of items to be displayed on a page.
        self.per_page = per_page
        #: the total number of items matching the query
        self.total = total
        #: the items for the current page
        self.items = items

    @property
    def pages(self):
        """The total number of pages"""
        if self.per_page == 0:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page."""
        return paginate(self.page - 1, self.per_page, error_out)

    @property
    def prev_num(self):
        """Number of the previous page."""
        if not self.has_prev:
            return None
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self, error_out=False):
        return paginate(self.page + 1, self.per_page, error_out)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        if not self.has_next:
            return None
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):

        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

    @property
    def to_json(self):
        return {'items': self.items,
                'has_prev': self.has_prev,
                'prev_num': self.prev_num,
                'has_next': self.has_next,
                'next_num': self.next_num,
                'iter_pages': list(self.iter_pages()),
                'pages': self.pages,
                'page': self.page,
                'total': self.total
                }


def paginate(list, page=1, per_page=3, max_per_page=None):
    if max_per_page is not None:
        per_page = min(per_page, max_per_page)
    start = (page-1) * per_page
    end = page*per_page
    items = list[start:end]
    total = len(list)
    return Pagination(page, per_page, total, items).to_json

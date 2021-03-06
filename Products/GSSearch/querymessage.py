# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright © 2012, 2013, 2014 OnlineGroups.net and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import sqlalchemy as sa
from gs.core import to_unicode_or_bust
from gs.database import getSession
from Products.XWFMailingListManager.queries import MessageQuery\
    as MailingListQuery


def topic_sorter_desc(x, y):
    if x['last_post_date'] < y['last_post_date']:
        return 1
    else:
        return -1


class MessageQuery(MailingListQuery):
    """Query the message database"""

# --=mpj17=-- We are moving the post-searching to gs.group.messages.posts

#lint:disable
    TOPIC_SEARCH = 1
    TOPIC_SEARCH_COUNT = 2
    POST_SEARCH = 4
    POST_SEARCH_COUNT = 8
#lint:enable

    def __init__(self, context):
        MailingListQuery.__init__(self, context)

    def add_standard_where_clauses(self, statement, table,
                                   site_id, group_ids, hidden):
        statement.append_whereclause(table.c.site_id == site_id)
        if group_ids:
            inStatement = table.c.group_id.in_(group_ids)
            statement.append_whereclause(inStatement)
        else:
            # --=mpj17=-- No, I am not smoking (much) crack. If the
            #  "group_ids" are not specified, I want to return nothing in
            #  all cases. However, I cannot append "False" to the
            #  statement, so I append two items that are mutually
            #  exclusive.
            statement.append_whereclause(table.c.group_id == '')
            statement.append_whereclause(table.c.group_id != '')
        if not(hidden):
            # We normally want to exclude hidden posts and topics.
            statement.append_whereclause(table.c.hidden == None)  # lint:ok
        return statement

    def __add_topic_keyword_search_where_clauses(self, statement, tokens):
        tt = self.topicTable
        if tokens.keywords:
            q = ' & '.join(tokens.keywords)
            statement.append_whereclause(tt.c.fts_vectors.match(q))
        assert statement is not None
        return statement

    def __add_post_keyword_search_where_clauses(self, statement,
      searchTokens):
        """Post searching is easier than topic searching, as there is no
          natural join between the topic and post tables."""
        pt = self.postTable
        if searchTokens.keywords:
            q = ' & '.join(searchTokens.keywords)
            statement.append_whereclause(pt.c.fts_vectors.match(q))
        assert statement is not None
        return statement

    def __add_author_where_clauses(self, statement, author_ids):
        pt = self.postTable
        author_ids = author_ids and [a for a in author_ids if a] or []
        if author_ids:
            statement.append_whereclause(pt.c.user_id.in_(author_ids))
        return statement

    def topic_search_keyword(self, searchTokens, site_id, group_ids=None,
                            limit=12, offset=0, use_cache=True, hidden=False):
        """ Search for the search text in the content and subject-lines of
        topics."""
        if group_ids is None:
            group_ids = []

        tt = self.topicTable
        tkt = self.topicKeywordsTable
        pt = self.postTable

        cols = [tt.c.topic_id, tt.c.last_post_id,
          tt.c.first_post_id, tt.c.group_id, tt.c.site_id, tkt.c.keywords,
          tt.c.original_subject, tt.c.last_post_date, tt.c.num_posts,
          sa.select([pt.c.user_id], tt.c.last_post_id ==
                                    pt.c.post_id).as_scalar().label('user_id')]
        statement = sa.select(cols, limit=limit, offset=offset,
                        order_by=sa.desc(tt.c.last_post_date))
        statement.append_whereclause(tkt.c.topic_id == tt.c.topic_id)
        statement = self.add_standard_where_clauses(statement,
                        self.topicTable, site_id, group_ids, False)
        statement = self.__add_topic_keyword_search_where_clauses(statement,
                                                              searchTokens)
        session = getSession()
        r = session.execute(statement)
        retval = []
        for x in r:
            retval.append({'topic_id': x['topic_id'],
                           'last_post_id': x['last_post_id'],
                           'first_post_id': x['first_post_id'],
                           'group_id': x['group_id'],
                           'site_id': x['site_id'],
                           'subject': x['original_subject'],
                           'keywords': [to_unicode_or_bust(k)
                                           for k in x['keywords']],
                           'last_post_date': x['last_post_date'],
                           'last_post_user_id': x['user_id'],
                           'num_posts': x['num_posts']})

        return retval

    def post_search_keyword(self, searchTokens, site_id, group_ids=None,
                            author_ids=None, limit=12, offset=0):
        if group_ids is None:
            group_ids = []
        if author_ids is None:
            author_ids = []
        pt = self.postTable
        cols = [pt.c.post_id, pt.c.user_id, pt.c.group_id, pt.c.subject,
                pt.c.date, pt.c.body, pt.c.has_attachments]
        statement = sa.select(cols, limit=limit, offset=offset,
                  order_by=sa.desc(pt.c.date))
        self.add_standard_where_clauses(statement, pt, site_id, group_ids,
                                        False)
        statement = self.__add_author_where_clauses(statement, author_ids)
        statement = self.__add_post_keyword_search_where_clauses(statement,
          searchTokens)

        session = getSession()
        r = session.execute(statement)
        retval = []
        for x in r:
            p = {
              'post_id': x['post_id'],
              'user_id': x['user_id'],
              'group_id': x['group_id'],
              'subject': x['subject'],
              'date': x['date'],
              'body': x['body'],
              'files_metadata': x['has_attachments']
                                  and self.files_metadata(x['post_id'])
                                  or [],
              }
            retval.append(p)
        return retval

    def post_ids_from_file_ids(self, fileIds, hidden=False):
        p = self.postTable
        f = self.fileTable
        statement = f.select()
        inStatement = f.c.file_id.in_(fileIds)
        statement.append_whereclause(inStatement)
        statement.append_whereclause(p.c.post_id == f.c.post_id)
        if not hidden:
            statement.append_whereclause(p.c.hidden == None)  # lint:ok

        session = getSession()
        r = session.execute(statement)
        retval = {}
        if r.rowcount:
            for x in r:
                retval[x['file_id']] = x['post_id']
        return retval

    def files_metadata_topic(self, topic_ids):
        ft = self.fileTable
        pt = self.postTable
        cols = [
          pt.c.site_id, pt.c.group_id, pt.c.topic_id, pt.c.user_id,
          ft.c.post_id, ft.c.file_id, ft.c.mime_type, ft.c.file_name,
          ft.c.file_size, ft.c.date]
        statement = sa.select(cols, ft.c.topic_id.in_(topic_ids),
                    order_by=self.fileTable.c.date)
        statement.append_whereclause(ft.c.post_id == pt.c.post_id)

        session = getSession()
        r = session.execute(statement)

        retval = [{
                  'site_id': x['site_id'],
                  'group_id': x['group_id'],
                  'topic_id': x['topic_id'],
                  'user_id': x['user_id'],
                  'post_id': x['post_id'],
                  'file_id': x['file_id'],
                  'file_size': x['file_size'],
                  'mime_type': x['mime_type'],
                  'file_name': x['file_name'],
                  'date': x['date'],
                  } for x in r]
        return retval

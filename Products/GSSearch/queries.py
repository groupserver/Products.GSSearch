# coding=utf-8
from datetime import datetime, timedelta
import sqlalchemy as sa
from sqlalchemy.exc import NoSuchTableError
from gs.database import getSession, getTable
from Products.XWFMailingListManager.queries import MessageQuery\
  as MailingListQuery

import logging
log = logging.getLogger('GSSearch')


def topic_sorter_desc(x, y):
    if x['last_post_date'] < y['last_post_date']:
        return 1
    else:
        return -1

#
# TOTALLY UNTESTED. A STARTING POINT FOR A FUTURE FileQuery implementation
#


class FileQuery(object):
    def __init__(self, context):
        self.context = context
        self.fileTable = getTable('file')
        self.postTable = getTable('post')

    def file_search(self, siteId, groupIds, authorIds, keywords, mimeTypes):
        ft = self.fileTable
        pt = self.postTable
        cols = [
          pt.c.site_id, pt.c.group_id, pt.c.topic_id, pt.c.user_id,
          ft.c.post_id, ft.c.file_id, ft.c.mime_type, ft.c.file_name,
          ft.c.file_size, ft.c.date]
        statement = sa.select(cols, ft.c.post_id == pt.c.post_id,
                              order_by=self.fileTable.c.date)

        if siteId:
            statement.append_whereclause(pt.c.site_id==siteId)  # lint:ok

        if groupIds:
            statement.append_whereclause(pt.c.group_id.in_(groupIds))

        if authorIds:
            statement.append_whereclause(pt.c.user_id.in_(authorIds))

        if mimeTypes:
            statement.append_whereclause(pt.c.mime_type.in_(mimeTypes))

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

#
# END OF TOTALLY UNTESTED FILE QUERY
#


def ck_simple(*args):
    return "REPLACEME" + '%'.join(map(str, args[1:]))


def ck_tsk(*args):
    return "REPLACEME" + '%'.join(map(str, args[2:]))


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
        try:
            self.rowcountTable = getTable('rowcount')
        except NoSuchTableError:
            self.rowcountTable = None

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
        return statement

    def __add_post_keyword_search_where_clauses(self, statement,
      searchTokens):
        """Post searching is easier than topic searching, as there is no
          natural join between the topic and post tables."""
        pt = self.postTable
        if searchTokens.keywords:
            q = ' & '.join(searchTokens.keywords)
            statement.append_whereclause(pt.c.fts_vectors.match(q))

    def __add_author_where_clauses(self, statement, author_ids):
        pt = self.postTable
        author_ids = author_ids and [a for a in author_ids if a] or []
        if author_ids:
            statement.append_whereclause(pt.c.user_id.in_(author_ids))
        return statement

    def topic_search_keyword(self, searchTokens, site_id,
        group_ids=[], limit=12, offset=0, use_cache=True, hidden=False):
        """ Search for the search text in the content and subject-lines of
        topics.

        """
        tt = self.topicTable
        pt = self.postTable

        cols = [tt.c.topic_id.distinct(), tt.c.last_post_id,
          tt.c.first_post_id, tt.c.group_id, tt.c.site_id, tt.c.keywords,
          tt.c.original_subject, tt.c.last_post_date, tt.c.num_posts,
          sa.select([pt.c.user_id], tt.c.last_post_id ==
                                    pt.c.post_id).as_scalar().label('user_id')]
        statement = sa.select(cols, limit=limit, offset=offset,
                        order_by=sa.desc(tt.c.last_post_date))

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
                           'keywords': x['keywords'],
                           'last_post_date': x['last_post_date'],
                           'last_post_user_id': x['user_id'],
                           'num_posts': x['num_posts']})

        return retval

    def count_topic_search_keyword(self, searchTokens, site_id,
        group_ids=[]):
        """Search for the search text in the content and subject-lines of
        topics"""
        tt = self.topicTable

        cols = [sa.func.count(tt.c.topic_id.distinct())]
        statement = sa.select(cols)
        statement = self.add_standard_where_clauses(statement, tt, site_id,
                                                    group_ids, False)
        statement = self.__add_topic_keyword_search_where_clauses(statement,
          searchTokens)

        session = getSession()
        r = session.execute(statement)
        retval = r.scalar()
        if retval is None:
            retval = 0
        assert retval >= 0

        return retval

    def post_search_keyword(self, searchTokens, site_id, group_ids=[],
        author_ids=[], limit=12, offset=0):
        pt = self.postTable
        cols = [pt.c.post_id.distinct(), pt.c.user_id, pt.c.group_id,
          pt.c.subject, pt.c.date, pt.c.body, pt.c.has_attachments]
        statement = sa.select(cols, limit=limit, offset=offset,
                  order_by=sa.desc(pt.c.date))
        self.add_standard_where_clauses(statement, pt, site_id,
            group_ids, False)
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

    def count_post_search_keyword(self, searchTokens,
        site_id, group_ids=[], author_ids=[]):
        pt = self.postTable

        cols = [sa.func.count(pt.c.post_id.distinct())]
        statement = sa.select(cols)
        self.add_standard_where_clauses(statement, pt, site_id,
            group_ids, False)
        statement = self.__add_author_where_clauses(statement, author_ids)
        statement = self.__add_post_keyword_search_where_clauses(statement,
          searchTokens)

        session = getSession()
        r = session.execute(statement)
        retval = r.scalar()
        if retval is None:
            retval = 0
        assert retval >= 0
        return retval

    def __row_count(self, table, tablename):
        retval = 0
        session = getSession()
        if self.rowcountTable is not None:
            statement = self.rowcountTable.select()
            statement.append_whereclause(self.rowcountTable.c.table_name ==
                                        tablename)
            r = session.execute(statement)
            if r.rowcount:
                retval = r.fetchone()['total_rows']
        if not retval:
            statement = sa.select([sa.func.count("*")], from_obj=[table])
            r = session.execute(statement)
            retval = r.scalar()
        return retval

    def count_topics(self):
        return self.__row_count(self.topicTable, 'topic')

    def count_posts(self):
        return self.__row_count(self.postTable, 'post')

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


class DigestQuery(MessageQuery):
    def topics_sinse_yesterday(self, siteId, groupIds):
        tt = self.topicTable
        pt = self.postTable
        yesterday = datetime.now() - timedelta(days=1)

        #SELECT topic.topic_id, topic.original_subject, topic.last_post_id,
        #  topic.last_post_date, topic.num_posts,
        cols = [tt.c.topic_id, tt.c.original_subject, tt.c.last_post_id,
                tt.c.last_post_date, tt.c.num_posts,
        #  (SELECT COUNT(*)
        #    FROM post
        #    WHERE (post.topic_id = topic.topic_id)
        #      AND post.date >= timestamp 'yesterday')
        #  AS num_posts_day
               sa.select([sa.func.count(pt.c.post_id.distinct())],
                         sa.and_(pt.c.date >= yesterday,
                         pt.c.topic_id == tt.c.topic_id)
                         ).as_scalar().label('num_posts_day'),
               sa.select([pt.c.user_id],
                         pt.c.post_id == tt.c.last_post_id
                         ).as_scalar().label('last_author_id')]
        s = sa.select(cols, order_by=sa.desc(tt.c.last_post_date))
        #  FROM topic
        #  WHERE topic.site_id = 'main'
        #    AND topic.group_id = 'mpls'
        s = self.add_standard_where_clauses(s, tt, siteId, groupIds,
                False)
        #    AND topic.last_post_date >= timestamp 'yesterday'
        s.append_whereclause(tt.c.last_post_date >= yesterday)

        session = getSession()
        r = session.execute(s)

        retval = [{
                  'topic_id': x['topic_id'],
                  'original_subject': x['original_subject'],
                  'last_post_id': x['last_post_id'],
                  'last_post_date': x['last_post_date'],
                  'num_posts': x['num_posts'],
                  'num_posts_day': x['num_posts_day'],
                  'last_author_id': x['last_author_id'],
                  } for x in r]
        return retval

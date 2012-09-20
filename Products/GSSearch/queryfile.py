# -*- coding: utf-8 *-*
#
# TOTALLY UNTESTED. A STARTING POINT FOR A FUTURE FileQuery implementation
#
import sqlalchemy as sa
from gs.database import getSession, getTable


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
            statement.append_whereclause(pt.c.site_id == siteId)  # lint:ok

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

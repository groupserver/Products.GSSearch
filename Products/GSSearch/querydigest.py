# -*- coding: utf-8 *-*
from datetime import datetime, timedelta
import sqlalchemy as sa
from gs.database import getSession
from querymessage import MessageQuery


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

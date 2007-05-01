import Products.XWFMailingListManager.queries
import sqlalchemy as sa

class MessageQuery(Products.XWFMailingListManager.queries.MessageQuery):
    """Query the message database"""
    
    def topic_search_subect(self, subjectStr, site_id, group_ids=[], 
        limit=12, offset=0):
        """Search for a particular subject in the list of topics."""
        
        statement = self.topicTable.select()
        aswc=Products.XWFMailingListManager.queries.MessageQuery.__add_std_where_clauses
        aswc(self, statement, self.topicTable, site_id, group_ids)
        
        subjCol = self.topicTable.c.original_subject
        regexp = '.*%s.*' % subjectStr.lower()
        statement.append_whereclause(subjCol.op('~*')(regexp))
        
        statement.limit = limit
        statement.offset = offset
        statement.order_by(sa.desc(self.topicTable.c.last_post_date))
        
        r = statement.execute()
        
        retval = []
        if r.rowcount:
            retval = [ {'topic_id': x['topic_id'],
                        'last_post_id': x['last_post_id'], 
                        'first_post_id': x['first_post_id'], 
                        'group_id': x['group_id'], 
                        'site_id': x['site_id'], 
                        'subject': unicode(x['original_subject'], 'utf-8'), 
                        'last_post_date': x['last_post_date'], 
                        'num_posts': x['num_posts']} for x in r ]
        
        return retval

    def topic_search_keyword(self, keyword, limit=12, offset=0):
        """Search for a particular keyword in the list of topics."""
        
        statement = self.topic_word_countTable.select()
        
        statement.append_whereclause(self.topic_word_countTable.c.word == \
          keyword)
        
        statement.limit = limit
        statement.offset = offset
        statement.order_by(sa.desc(self.topic_word_countTable.c.count))
        
        r = statement.execute()
        
        retval = []
        if r.rowcount:
            retval = [ {'topic_id': x['topic_id'], 
                        'word': unicode(x['word'], 'utf-8'), 
                        'count': x['count']} for x in r ]
        
        return retval


import Products.XWFMailingListManager.queries
import sqlalchemy as sa

class MessageQuery(Products.XWFMailingListManager.queries.MessageQuery):
    """Query the message database"""
    
    def topic_search_subect(self, subjectStr, limit=12, offset=0):
        """Search for a particular subject in the list of topics."""
        
        statement = self.topicTable.select()
        
        subjCol = self.topicTable.c.original_subject
        statement.append_whereclause(subjCol.like('%%%s%%' % subjectStr))
        
        statement.limit = limit
        statement.offset = offset
        statement.order_by(sa.desc(self.topicTable.c.last_post_date))
        
        r = statement.execute()
        
        retval = []
        if r.rowcount:
            retval = [ {'last_post_id': x['last_post_id'], 
                        'first_post_id': x['first_post_id'], 
                        'group_id': x['group_id'], 
                        'site_id': x['site_id'], 
                        'subject': unicode(x['original_subject'], 'utf-8'), 
                        'date': x['last_post_date'], 
                        'num_posts': x['num_posts']} for x in r ]
        
        return retval


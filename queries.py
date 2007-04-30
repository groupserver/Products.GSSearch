import Products.XWFMailingListManager.queries
import sqlalchemy as sa

class MessageQuery(Products.XWFMailingListManager.queries.MessageQuery):
    """Query the message database"""
    
    def topic_search_subect(self, subjectStr, limit=12, offset=0):
        """Search for a particular subject in the list of topics."""
        
        statement = self.topicTable.select()
        
        statement.append_whereclause(subjectStr ==
          self.topicTable.c.original_subject)
        
        statement.limit = limit
        statement.offset = offset
        statement.order_by(sa.desc(self.topicTable.c.last_post_date))
        
        r = statement.execute
        
        return []


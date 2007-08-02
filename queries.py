import Products.XWFMailingListManager.queries
from sqlalchemy.exceptions import NoSuchTableError
import sqlalchemy as sa
from Products.XWFCore import cache
import datetime

class MessageQuery(Products.XWFMailingListManager.queries.MessageQuery):
    """Query the message database"""

    # a cache for the count of keywords across the whole database, keyed
    # by the name of the database, since we might have more than one.
    # The cache structure is:
    #
    # {'object': wordcounts, 'expires': datetime)
    cache_wordCount = cache.SimpleCacheWithExpiry()
    cache_wordCount.set_expiry_interval(datetime.timedelta(0,3600)) # 1 hour 

    def __init__(self, context, da):
        super_query = Products.XWFMailingListManager.queries.MessageQuery
        super_query.__init__(self, context, da)

        session = da.getSession()
        metadata = session.getMetaData()

        self.word_countTable = da.createMapper('word_count')[1]

        try:
            self.rowcountTable = da.createMapper('rowcount')[1]
        except NoSuchTableError:
            self.rowcountTable = None    

        # useful for cache
        self.dbname = da.getProperty('database')
        self.now = datetime.datetime.now()

    def add_standard_where_clauses(self, statement, table, 
                                   site_id, group_ids):
        statement.append_whereclause(table.c.site_id==site_id)
        if group_ids:
            inStatement = table.c.group_id.in_(*group_ids)
            statement.append_whereclause(inStatement)
        else:
            # --=mpj17=-- No, I am not smoking (much) crack. If the 
            #  "group_ids" are not specified, I want to return nothing in
            #  all cases. However, I cannot append "False" to the 
            #  statement, so I append two items that are mutually 
            #  exclusive.
            statement.append_whereclause(table.c.group_id == '')
            statement.append_whereclause(table.c.group_id != '')
            
        return statement

    def topic_search_keyword(self, searchTokens, site_id, 
        group_ids=[], limit=12, offset=0):
        """Search for the search text in the content and subject-lines of
        topics"""

        tt = self.topicTable
        pt = self.postTable
        wct = self.topic_word_countTable

        cols = [tt.c.topic_id.distinct(), tt.c.last_post_id, 
          tt.c.first_post_id,  tt.c.group_id, tt.c.site_id, 
          tt.c.original_subject,  tt.c.last_post_date, tt.c.num_posts, 
          pt.c.user_id]
        statement = sa.select(cols, tt.c.last_post_id == pt.c.post_id)

        self.add_standard_where_clauses(statement, self.topicTable, 
          site_id, group_ids)
          
        topicIdCol = self.topicTable.c.topic_id
        
        if searchTokens.phrases:
            # post.topic_id = topic_word_count.topic_id 
            statement.append_whereclause(pt.c.topic_id == wct.c.topic_id)
            
            # topic_word_count.word IN ('blog','exposure') 
            clause = wct.c.word.in_(*searchTokens.keywords)
            statement.append_whereclause(clause)
            
            if (len(searchTokens.phrases) != len(searchTokens.keywords)):
                # Do a phrase search. *Shudder*
                # post.topic_id=topic.topic_id
                clause = (pt.c.topic_id == tt.c.topic_id)
                
                # post.body ~* '(blog exposure)')
                brackets = ['(%s)' % k for k in searchTokens.phrases]
                regularExpression = '|'.join(brackets)
                clause1 = pt.c.body.op('~*')(regularExpression)

                statement.append_whereclause(sa.and_(clause, clause1))

        statement.limit = limit
        statement.offset = offset
        statement.order_by(sa.desc(self.topicTable.c.last_post_date))        

        r = statement.execute()
        retval = []
        for x in r:
            retval.append(
                {'topic_id': x['topic_id'],
                 'last_post_id': x['last_post_id'], 
                 'first_post_id': x['first_post_id'], 
                 'group_id': x['group_id'], 
                 'site_id': x['site_id'], 
                 'subject': unicode(x['original_subject'], 'utf-8'), 
                 'last_post_date': x['last_post_date'], 
                 'last_post_user_id': x['user_id'],
                 'num_posts': x['num_posts']})
        return retval
    
    def count_topic_search_keyword(self, searchTokens, site_id, 
        group_ids=[]):
        """Search for the search text in the content and subject-lines of
        topics"""

        cols = [sa.func.count(self.topicTable.c.topic_id.distinct())]
        statement = sa.select(cols)
        
        self.add_standard_where_clauses(statement, self.topicTable, 
          site_id, group_ids)
          
        pt = self.postTable        
        wct = self.topic_word_countTable
        topicIdCol = self.topicTable.c.topic_id
        if (searchTokens.keywords and
            (len(searchTokens.keywords) != len(searchTokens.phrases))):
            # Do a phrase search. *shudder*
            s2 = sa.select([wct.c.topic_id.distinct()], 
                            wct.c.word.in_(*searchTokens.keywords))
            brackets = ['(%s)' % k for k in searchTokens.phrases]
            regularExpression = '|'.join(brackets)
            s2.append_whereclause(pt.c.body.op('~*')(regularExpression))
            statement.append_whereclause(topicIdCol.in_(s2))
        elif searchTokens.keywords:
            s2 = sa.select([wct.c.topic_id.distinct()], 
                           wct.c.word.in_(*searchTokens.keywords))
            statement.append_whereclause(topicIdCol.in_(s2))
            
        r = statement.execute()
        retval = r.scalar()
        if retval == None:
            retval = 0
        assert retval >= 0
        return retval

    def __row_count(self, table, tablename):
        count = 0
        if self.rowcountTable:
            statement = self.rowcountTable.select()
            statement.append_whereclause(self.rowcountTable.c.table_name==tablename)
            r = statement.execute()
            if r.rowcount:
                count = r.fetchone()['total_rows']
        
        if not count:
            statement = sa.select([sa.func.count("*")], from_obj=[table])
            r = statement.execute()
            count = r.scalar()
        
        return count

    def count_topics(self):
        return self.__row_count(self.topicTable, 'topic')

    def count_posts(self):
        return self.__row_count(self.postTable, 'post')
        
    def word_counts(self):
        retval = self.cache_wordCount.get(self.dbname)
        if not retval:
            statement = self.word_countTable.select()
            # The following where clause speeds up the query: we will assume 1
            #   later on, if the word is not in the dictionary.
            statement.append_whereclause(self.word_countTable.c.count > 1)
            r = statement.execute()
            retval = {}
            if r.rowcount:
                for x in r:
                    retval[unicode(x['word'], 'utf-8')] = x['count']
            
            self.cache_wordCount.add(self.dbname, retval)
        
        return retval
        
    def count_total_topic_word(self, word):
        """Count the total number of topics that contain a particular word"""
        countTable = self.word_countTable
        statement = countTable.select()
        statement.append_whereclause(countTable.c.word == word)

        r = statement.execute()
        retval = 0
        if r.rowcount:
            v = [{'count': x['count']} for x in r]
            retval = v[0]['count']
        return retval

    def count_words(self):
        countTable = self.word_countTable
        statement = sa.select([sa.func.sum(countTable.c.count)])
        r = statement.execute()
        return r.scalar()
        
    def count_word_in_topic(self, word, topicId):
        """Count the number of times word occurs in a topic"""
        countTable = self.topic_word_countTable
        statement = sa.select([countTable.c.count])
        statement.append_whereclause(countTable.c.topic_id == topicId)
        statement.append_whereclause(countTable.c.word == word)
        r = statement.execute()
        retval = 0
        if r.rowcount:
            val = [{'count': x['count']} for x in r]
            retval = val[0]['count']
        return retval

    def topics_word_count(self, topicIds):
        """Get a count for all the words in a list of topics
        
        DESCRIPTION
          Returns the count of the topics specified by the list "topicIds".
          However, for the sake of speed, words with a count of 1 are not
          returned.
          
        RETURNS
          A list of dictionaries. Each dictionary contains three values:
            * "topic_id" The ID of the topic,
            * "word" A word in the topic, and
            * "count" The count of "word" in the topic (always greater than
              one).
        """
        countTable = self.topic_word_countTable
        statement = countTable.select()
        if topicIds:
            inStatement = countTable.c.topic_id.in_(*topicIds)
            statement.append_whereclause(inStatement)
        statement.append_whereclause(countTable.c.count > 1)
        r = statement.execute()
        retval = []
        if r.rowcount:
            retval = [{'topic_id': x['topic_id'],
                       'word': x['word'],
                       'count': x['count']} for x in r]
        return retval

    def post_ids_from_file_ids(self, fileIds):
        statement = self.fileTable.select()
        inStatement = self.fileTable.c.file_id.in_(*fileIds)
        statement.append_whereclause(inStatement)
        r = statement.execute()
        retval = {}
        if r.rowcount:
            for x in r:
                retval[x['file_id']] = x['post_id']
        return retval

    def post_search_keyword(self, searchTokens, site_id, group_ids=[], 
        author_ids=[], limit=12, offset=0):
        
        statement = self.postTable.select()
        self.add_standard_where_clauses(statement, self.postTable, 
          site_id, group_ids)
                    
        author_ids = author_ids and [a for a in author_ids if a] or []
        authorCol = self.postTable.c.user_id
        if (len(author_ids) == 1):
            statement.append_whereclause(authorCol == author_ids[0])
        elif (len(author_ids) > 1):
            # For each author, construct a regular expression match, and 
            #   "or" them all together
            conds = [authorCol == a for a in author_ids]
            statement.append_whereclause(sa.or_(*conds))
        else: # (len(authorId) == 0)
            # We do not need to do anything if there are no authors
            pass

        if searchTokens.keywords:
            wct = self.topic_word_countTable
            s2 = sa.select([wct.c.topic_id.distinct()], 
                           wct.c.word.in_(*searchTokens.keywords))
            topicIdCol = self.postTable.c.topic_id
            statement.append_whereclause(topicIdCol.in_(s2))
            
        bodyCol = self.postTable.c.body
        subjectCol = self.postTable.c.subject

        if (len(searchTokens.phrases) >= 1):
            # For each keyword, construct a regular expression match that
            #   will "or" them all together
            brackets = ['(%s)' % k for k in searchTokens.phrases]
            regularExpression = '|'.join(brackets)
            statement.append_whereclause(bodyCol.op('~*')(regularExpression))
        else: # (len(keywords) == 0)
            # We do not need to do anything if there are no keywords
            pass

        statement.limit = limit
        statement.offset = offset
        statement.order_by(sa.desc(self.postTable.c.date))
        
        r = statement.execute()

        for x in r:
            retval = {
              'post_id':          x['post_id'],
              'user_id':          x['user_id'],
              'group_id':         x['group_id'],
              'subject':          x['subject'],
              'date':             x['date'],
              'body':             x['body'],
              'files_metadata':   x['has_attachments'] 
                                  and self.files_metadata(x['post_id']) 
                                  or [],
              }
            yield retval

    def count_post_search_keyword(self, searchTokens, 
        site_id, group_ids=[], author_ids=[]):
        
        statement = sa.select([sa.func.count(self.postTable.c.post_id)])
        self.add_standard_where_clauses(statement, self.postTable, 
          site_id, group_ids)
                    
        author_ids = author_ids and [a for a in author_ids if a] or []
        authorCol = self.postTable.c.user_id
        if (len(author_ids) == 1):
            statement.append_whereclause(authorCol == author_ids[0])
        elif (len(author_ids) > 1):
            # For each author, construct a regular expression match, and 
            #   "or" them all together
            conds = [authorCol == a for a in author_ids]
            statement.append_whereclause(sa.or_(*conds))
        else: # (len(authorId) == 0)
            # We do not need to do anything if there are no authors
            pass

        if searchTokens.keywords:
            wct = self.topic_word_countTable
            s2 = sa.select([wct.c.topic_id.distinct()], 
                           wct.c.word.in_(*searchTokens.keywords))
            topicIdCol = self.postTable.c.topic_id
            statement.append_whereclause(topicIdCol.in_(s2))
            
        bodyCol = self.postTable.c.body
        subjectCol = self.postTable.c.subject

        if (len(searchTokens.phrases) >= 1):
            # For each keyword, construct a regular expression match that
            #   will "or" them all together
            brackets = ['(%s)' % k for k in searchTokens.phrases]
            regularExpression = '|'.join(brackets)
            statement.append_whereclause(bodyCol.op('~*')(regularExpression))
        else: # (len(keywords) == 0)
            # We do not need to do anything if there are no keywords
            pass

        r = statement.execute()
        retval = r.scalar()
        if retval == None:
            retval = 0
        assert retval >= 0
        return retval

    def files_metata_topic(self, topic_ids):
        ft = self.fileTable
        pt = self.postTable
        cols = [
          pt.c.site_id, pt.c.group_id, pt.c.topic_id, pt.c.user_id, 
          ft.c.post_id, ft.c.file_id, ft.c.mime_type, ft.c.file_name,
          ft.c.file_size, ft.c.date,]
        statement = sa.select(cols, ft.c.topic_id.in_(*topic_ids))
        statement.append_whereclause(ft.c.post_id == pt.c.post_id)
        statement.order_by(self.fileTable.c.date)

        r = statement.execute()
        
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


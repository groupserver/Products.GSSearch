import Products.XWFMailingListManager.queries
import sqlalchemy as sa

class MessageQuery(Products.XWFMailingListManager.queries.MessageQuery):
    """Query the message database"""

    def __init__(self, context, da):
        super_query = Products.XWFMailingListManager.queries.MessageQuery
        super_query.__init__(self, context, da)

        session = da.getSession()
        metadata = session.getMetaData()

        self.word_countTable = sa.Table('word_count', metadata, 
          autoload=True)
    
    def topic_search_subect(self, keywords, site_id, group_ids=[], 
        limit=12, offset=0):
        """Search for a particular subject in the list of topics."""
        
        statement = self.topicTable.select()
        sc = Products.XWFMailingListManager.queries.MessageQuery
        aswc = sc.__add_std_where_clauses
        aswc(self, statement, self.topicTable, site_id, group_ids)
        
        subjCol = self.topicTable.c.original_subject

        if (len(keywords) == 1):
            regexp = '.*%s.*' % keywords[0].lower()
            statement.append_whereclause(subjCol.op('~*')(regexp))
        elif (len(keywords) > 1):
            # For each keyword, construct a regular expression match
            #   against the subject, and or them all together
            regexp = r'.*%s.*'
            conds = [subjCol.op('~*')(regexp % k ) for k in keywords]
            statement.append_whereclause(sa.or_(*conds))
        else: # (len(keywords) == 0)
            # We do not need to do anything if there are no keywords
            pass
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

    def topic_search_keyword(self, keywords, site_id, group_ids=[],
        limit=12, offset=0):
        """Search for a particular keyword in the list of topics."""
        
        countTable = self.topic_word_countTable
        
        cols = [self.topicTable.c.topic_id, self.topicTable.c.group_id,
          self.topicTable.c.site_id, self.topicTable.c.original_subject,
          self.topicTable.c.first_post_id, self.topicTable.c.last_post_id,
          self.topicTable.c.last_post_date, self.topicTable.c.num_posts]
        statement = sa.select(cols, 
          self.topicTable.c.topic_id == countTable.c.topic_id)

        sc = Products.XWFMailingListManager.queries.MessageQuery
        aswc = sc.__add_std_where_clauses
        aswc(self, statement, self.topicTable, site_id, group_ids)

        if (len(keywords) == 1):
            regexep = keywords[0].lower()
            #statement.append_whereclause(countTable.c.word.op('~*')(regexep))
            statement.append_whereclause(countTable.c.word == regexep)
        elif(len(keywords) > 1):
            #conds = [(countTable.c.word.op('~*')(k.lower())) for k in keywords]
            conds = [(countTable.c.word == k.lower()) for k in keywords]
            statement.append_whereclause(sa.or_(*conds))
        else: # (len(keywords) == 0)
            # We do not need to do anything if there are no keywords.
            pass
        statement.limit = limit
        statement.offset = offset
        statement.order_by(sa.desc(self.topicTable.c.last_post_date))
        statement.distinct = True
        
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

    def topic_search_keyword_subject(self, keywords, site_id, 
        group_ids=[], limit=12, offset=0):
        """Search for the search text in the content and subject-lines of
        topics"""
        
        cols = [self.topicTable.c.topic_id.distinct(), 
          self.topicTable.c.group_id, self.topicTable.c.site_id,
          self.topicTable.c.original_subject,
          self.topicTable.c.first_post_id, self.topicTable.c.last_post_id,
          self.topicTable.c.last_post_date, self.topicTable.c.num_posts]
        statement = sa.select(cols, 
          self.topicTable.c.topic_id == self.topic_word_countTable.c.topic_id)

        aswc=Products.XWFMailingListManager.queries.MessageQuery.__add_std_where_clauses
        aswc(self, statement, self.topicTable, site_id, group_ids)

        subjectCol = self.topicTable.c.original_subject
        wordCol = self.topic_word_countTable.c.word
        if (len(keywords) == 1):
            regexp = keywords[0].lower()
            conds = (subjectCol.op('~*')(regexp), wordCol == regexp)
            statement.append_whereclause(sa.or_(*conds))
        elif (len(keywords) > 1):
            # For each keyword, construct a regular expression match, and 
            #   "or" them all together
            subjectConds = [subjectCol.op('~*')(k ) for k in keywords]
            wordConds = [(wordCol == k) for k in keywords]
            conds = subjectConds + wordConds
            statement.append_whereclause(sa.or_(*conds))
        else: # (len(keywords) == 0)
            # We do not need to do anything if there are no keywords
            pass

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
    
    def count_topics(self):
        countTable = self.topicTable
        statement = sa.select([sa.func.count(countTable.c.topic_id)])
        r = statement.execute()
        return r.scalar()
        
    def word_counts(self):
        statement = self.word_countTable.select()
        # The following where clause speeds up the query: we will assume 1
        #   later on, if the word is not in the dictionary.
        statement.append_whereclause(self.word_countTable.c.count > 1)
        r = statement.execute()
        retval = {}
        if r.rowcount:
            for x in r:
                retval[unicode(x['word'], 'utf-8')] = x['count']
        return retval
        
    def count_total_topic_word(self, word):
        """Count the totoal number of topics that contain a particular word"""
        countTable = self.word_countTable
        statement = countTable.select()
        statement.append_whereclause(countTable.c.word == word)

        r = statement.execute()
        retval = 0
        if r.rowcount:
            v = [{'count': x['count']} for x in r]
            print len(v)
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

    def post_search_keyword(self, keywords, site_id, group_ids=[], 
        author_ids=[], limit=12, offset=0):
        
        statement = self.postTable.select()
        sc = Products.XWFMailingListManager.queries.MessageQuery
        aswc = sc.__add_std_where_clauses
        aswc(self, statement, self.postTable, site_id, group_ids)
        
        bodyCol = self.postTable.c.body
        subjectCol = self.postTable.c.subject

        keywords = [k for k in keywords if k]
        if (len(keywords) == 1):
            regexp = keywords[0].lower()
            conds = (subjectCol.op('~*')(regexp), bodyCol.op('~*')(regexp))
            statement.append_whereclause(sa.or_(*conds))
        elif (len(keywords) > 1):
            # For each keyword, construct a regular expression match, and 
            #   "or" them all together
            subjectConds = [subjectCol.op('~*')(k ) for k in keywords]
            bodyConds = [bodyCol.op('~*')(k ) for k in keywords]
            conds = subjectConds + bodyConds
            statement.append_whereclause(sa.or_(*conds))
        else: # (len(keywords) == 0)
            # We do not need to do anything if there are no keywords
            pass

        author_ids = [a for a in author_ids if a]
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

        
        topics = self.topic_search_keyword_subject(keywords, site_id,
           group_ids, limit, offset)
        # --=mpj17=-- Need to search the subject-line of the topics.
        conds = [(self.postTable.c.topic_id == t['topic_id']) 
                 for t in topics]
        statement.append_whereclause(sa.or_(*conds))
        
        statement.limit = limit
        statement.offset = offset
        statement.order_by(sa.desc(self.postTable.c.date))
        
        r = statement.execute()
        for x in r:
            retval = {
              'post_id': x['post_id'],
              'user_id': x['user_id'],
              'group_id': x['group_id'],
              'subject': x['subject'],
              'date':    x['date'],
              'body':    x['body'],
              }
            yield retval


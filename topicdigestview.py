#coding: utf-8
from zope.interface import implements, providedBy, Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.component import createObject, adapts, provideAdapter
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from queries import MessageQuery
import Globals
from Products.Five import BrowserView

class TopicDigestView(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        
        self.da = da = self.context.zsqlalchemy 
        assert da, 'No data-adaptor found'
        self.messageQuery = MessageQuery(context, da)
    
        self.stats = None
        
    def __call__(self):
        retval = u''
        
        assert type(retval) == unicode
        return retval

    def digest_query(self):    
        #SELECT topic.topic_id, topic.original_subject, topic.last_post_id, 
        #  topic.last_post_date, topic.num_posts,
        #  (SELECT COUNT(*) 
        #    FROM post 
        #    WHERE (post.topic_id = topic.topic_id) 
        #      AND post.date > timestamp 'yesterday') 
        #  AS num_posts_day
        #  FROM topic 
        #  WHERE topic.site_id = 'main' 
        #    AND topic.group_id = 'mpls' 
        #    AND topic.last_post_date > timestamp 'yesterday'
        #  ORDER BY topic.last_post_date DESC;


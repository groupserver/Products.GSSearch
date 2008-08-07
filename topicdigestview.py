#coding: utf-8
from textwrap import TextWrapper
from zope.interface import implements, providedBy, Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.component import createObject, adapts, provideAdapter
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from queries import DigestQuery
import Globals
from Products.Five import BrowserView
from Products.XWFCore.XWFUtils import date_format_by_age, change_timezone

class TopicDigestView(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        
        self.da = da = self.context.zsqlalchemy 
        assert da, 'No data-adaptor found'
        self.messageQuery = DigestQuery(context, da)
        
        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupInfo = createObject('groupserver.GroupInfo', context)
        
        self.topics = self.digest_query()
        
    def post_stats(self):
        retval = {'newTopics': 0,
                  'existingTopics': 0,
                  'newPosts':  0}
        for topic in self.topics:
            if topic['num_posts_day'] == topic['num_posts']:
                retval['newTopics'] = retval['newTopics'] + 1
            else:
                retval['existingTopics'] = retval['existingTopics'] + 1
            retval['newPosts'] = retval['newPosts'] + topic['num_posts_day']
        assert type(retval) == dict, 'Not a dict'
        assert 'newTopics'       in retval.keys()
        assert 'existingTopics'  in retval.keys()
        assert 'newPosts'        in retval.keys()
        return retval
        
    def __call__(self):
        retval = u''
        subjectWrap = TextWrapper(initial_indent     = u'* ', 
                                  subsequent_indent  = u'  ')
        metadataWrap = TextWrapper(initial_indent    = u'  o ',
                                   subsequent_indent = u'    ')
        groupTz = self.groupInfo.get_property('group_tz', 'UTC')
        for topic in self.topics:
            lastAuthor = createObject('groupserver.UserFromId', 
                                      self.context, 
                                      topic['last_author_id'])
            topic['last_author_name'] = lastAuthor.name
            subjectLine = subjectWrap.fill(topic['original_subject'])

            url = u'%s/r/topic/%s' % (self.siteInfo.url, 
                                       topic['last_post_id'])
            linkLine = metadataWrap.fill(url)
            
            dt = change_timezone(topic['last_post_date'], groupTz)
            topic['date'] = dt.strftime(date_format_by_age(dt))
            metadata = u'%(num_posts_day)s of %(num_posts)s posts since '\
              u'yesterday — latest at %(date)s by %(last_author_name)s' %\
              topic
            metadataLine = metadataWrap.fill(metadata)
            
            t = u'\n'.join((subjectLine, linkLine, metadataLine))
            retval = u'%s%s\n\n' % (retval, t)
            
        assert type(retval) == unicode
        return retval

    def digest_query(self):
        return self.messageQuery.topics_sinse_yesterday(self.siteInfo.id,
                                                        [self.groupInfo.id])


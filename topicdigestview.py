#coding: utf-8
from zope.interface import implements, providedBy, Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.component import createObject, adapts, provideAdapter
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from queries import DigestQuery
import Globals
from Products.Five import BrowserView
from Products.XWFCore.XWFUtils import munge_date

class TopicDigestView(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        
        self.da = da = self.context.zsqlalchemy 
        assert da, 'No data-adaptor found'
        self.messageQuery = DigestQuery(context, da)
        
        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupInfo = createObject('groupserver.GroupInfo', context)
        
    def __call__(self):
        retval = u''
        for topic in self.digest_query():
            topic['date'] = munge_date(self.groupInfo.groupObj, 
                                       topic['last_post_date'])
            lastAuthor = createObject('groupserver.UserFromId', 
                                      self.context, 
                                      topic['last_author_id'])
            topic['last_author_name'] = lastAuthor.name
            topic['link'] = u'%s/r/topic/%s' % (self.siteInfo.url, 
                                          topic['last_post_id'])
            t = '* %(original_subject)s\n    '\
              u'o %(num_posts_day)s of %(num_posts)s posts since yesterday '\
              u'-- latest at %(date)s by %(last_author_name)s\n    '\
              u'o %(link)s\n\n' % topic
            retval = u'%s%s\n' % (retval, t)
        assert type(retval) == unicode
        return retval

    def digest_query(self):
        return self.messageQuery.topics_sinse_yesterday(self.siteInfo.id,
                                                        [self.groupInfo.id])


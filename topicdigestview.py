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
from datetime import datetime, timedelta
import pytz

class TopicDigestView(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        
        self.da = da = self.context.zsqlalchemy 
        assert da, 'No data-adaptor found'
        self.messageQuery = DigestQuery(context, da)
        
        self.siteInfo = createObject('groupserver.SiteInfo', context)
        self.groupInfo = createObject('groupserver.GroupInfo', context)

        self.subjectWrap = TextWrapper(initial_indent     = u'* ', 
                                       subsequent_indent  = u'  ')
        self.metadataWrap = TextWrapper(initial_indent    = u'  o ',
                                        subsequent_indent = u'    ')
        self.groupTz = self.groupInfo.get_property('group_tz', 'UTC')
        
        self.__dailyDigestQuery = self.__weeklyDigestQuery = None
        self.topics = None

    def post_stats(self):
        retval = {'newTopics': 0,
                  'existingTopics': 0,
                  'newPosts':  0}
        for topic in self.topics:
            numPostsDay = topic.get('num_posts_day', 0)
            if numPostsDay and (numPostsDay == topic['num_posts']):
                retval['newTopics'] = retval['newTopics'] + 1
            else:
                retval['existingTopics'] = retval['existingTopics'] + 1
            retval['newPosts'] = retval['newPosts'] + numPostsDay
        assert type(retval) == dict, 'Not a dict'
        assert 'newTopics'       in retval.keys()
        assert 'existingTopics'  in retval.keys()
        assert 'newPosts'        in retval.keys()
        return retval
        
    def __call__(self):
        retval = u''
        if self.show_daily_digest():
            retval = self.daily_digest()
        elif self.show_weekly_digest():
            retval = self.weekly_digest()
        assert type(retval) == unicode
        return retval

    def show_daily_digest(self):
        '''Show the daily digest of topics. 
        
        This is not too hard to figure out: are there posts made in the
        last day?
        '''
        retval = (self.dailyTopics != [])
        assert type(retval) == bool
        return retval

    def show_weekly_digest(self):
        '''Show the weekly digest of topics.
        
        The weekly digest of topics is sent out on the weekly aniversary
        of the most recent post to the group.
        '''
        retval = (self.dailyTopics == []) \
          and (self.weeklyTopics != []) \
          and (datetime.now(pytz.UTC).strftime('%w') == \
               self.weeklyTopics[0]['last_post_date'].strftime('%w'))
        assert type(retval) == bool
        return retval

    def daily_digest(self):
        retval = u''
        for topic in self.dailyTopics:
            lastAuthor = createObject('groupserver.UserFromId', 
                                      self.context, 
                                      topic['last_author_id'])
            topic['last_author_name'] = lastAuthor.name
            subjectLine = self.subjectWrap.fill(topic['original_subject'])

            url = u'%s/r/topic/%s' % (self.siteInfo.url, 
                                       topic['last_post_id'])
            linkLine = self.metadataWrap.fill(url)
            
            dt = change_timezone(topic['last_post_date'], self.groupTz)
            topic['date'] = dt.strftime(date_format_by_age(dt))
            metadata = u'%(num_posts_day)s of %(num_posts)s posts since '\
              u'yesterday — latest at %(date)s by %(last_author_name)s' %\
              topic
            metadataLine = self.metadataWrap.fill(metadata)
            
            t = u'\n'.join((subjectLine, linkLine, metadataLine))
            retval = u'%s%s\n\n' % (retval, t)
        assert type(retval) == unicode
        return retval

    def weekly_digest(self):
        retval = u''
        topics = self.weeklyTopics
        lastWeek = datetime.now(pytz.UTC) - timedelta(days=7)
        if topics and (topics[0]['last_post_date'] <   lastWeek):
            for topic in topics:
                lastAuthor = createObject('groupserver.UserFromId', 
                                          self.context, 
                                          topic['last_post_user_id'])
                topic['last_author_name'] = lastAuthor.name
                subjectLine = self.subjectWrap.fill(topic['subject'])

                url = u'%s/r/topic/%s' % (self.siteInfo.url, 
                                           topic['last_post_id'])
                linkLine = self.metadataWrap.fill(url)
                
                dt = change_timezone(topic['last_post_date'], self.groupTz)
                topic['date'] = dt.strftime(date_format_by_age(dt))
                metadata = u'Latest post at %(date)s by '\
                  u'%(last_author_name)s' % topic
                metadataLine = self.metadataWrap.fill(metadata)

                t = u'\n'.join((subjectLine, linkLine, metadataLine))
                retval = u'%s%s\n\n' % (retval, t)
            
        assert type(retval) == unicode
        return retval
        
    @property
    def dailyTopics(self):
        if self.__dailyDigestQuery == None:
            self.__dailyDigestQuery = \
                self.messageQuery.topics_sinse_yesterday(
                    self.siteInfo.id, [self.groupInfo.id])
        retval =  self.topics = self.__dailyDigestQuery
        assert type(retval) == list
        return retval

    @property
    def weeklyTopics(self):
        if self.__weeklyDigestQuery == None:
            searchTokens = createObject('groupserver.SearchTextTokens', 
                self.context)
            searchTokens.set_search_text(u'')
            self.__weeklyDigestQuery = \
                self.messageQuery.topic_search_keyword(searchTokens, 
                    self.siteInfo.id, [self.groupInfo.id], limit=7, 
                    offset=0, use_cache=True)
        retval = self.topics = self.__weeklyDigestQuery
        assert type(retval) == list
        return retval


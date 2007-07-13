import sys, re, datetime, time, types, string, math, sha
from sets import Set
import Products.Five, DateTime, Globals
import zope.schema
from zope.component import createObject
import zope.app.pagetemplate.viewpagetemplatefile
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
import zope.interface, zope.component, zope.publisher.interfaces
import zope.viewlet.interfaces, zope.contentprovider.interfaces 

from Products.XWFMailingListManager.stopwords import en as STOP_WORDS

from Products.PythonScripts.standard import html_quote
import DocumentTemplate

import Products.XWFMailingListManager.view
import Products.GSContent, Products.XWFCore.XWFUtils
from interfaces import IGSTopicResultsContentProvider
from queries import MessageQuery
from Products.GSContent.interfaces import IGSSiteInfo, IGSGroupsInfo

from Products.XWFCore import cache

def tfidf_sort(a, b):
    if a['tfidf'] < b['tfidf']:
        retval = 1
    elif a['tfidf'] == b['tfidf']:
        retval = 0
    else:
        retval = -1
    return retval
    
class GSTopicResultsContentProvider(object):
      """GroupServer Topic Search-Results Content Provider
      """

      zope.interface.implements( IGSTopicResultsContentProvider )
      zope.component.adapts(zope.interface.Interface,
          zope.publisher.interfaces.browser.IDefaultBrowserLayer,
          zope.interface.Interface)

      cache_topicsWordCounts = cache.SimpleCache()
      
      def __init__(self, context, request, view):
          self.__parent__ = self.view = view
          self.__updated = False
      
          self.context = context
          self.request = request
          
      def update(self):
          self.__updated = True

          self.da = self.context.zsqlalchemy 
          assert self.da, 'No data-adaptor found'
          
          dbname = self.da.getProperty('database')

          self.messageQuery = MessageQuery(self.context, self.da)

          postCount = self.messageQuery.count_posts()

          self.siteInfo = createObject('groupserver.SiteInfo', 
            self.context)
          self.groupsInfo = createObject('groupserver.GroupsInfo', 
            self.context)
          self.searchTokens = createObject('groupserver.SearchTextTokens',
            self.searchText)          
          
          self.groupIds = [gId for gId in self.groupIds if gId]
          if self.groupIds:
              groupIds = self.groupsInfo.filter_visible_group_ids(self.groupIds)
          else:
              groupIds = self.groupsInfo.get_visible_group_ids()

          self.topics = self.messageQuery.topic_search_keyword(
            self.searchTokens, self.siteInfo.get_id(), 
            groupIds, limit=self.limit, offset=self.startIndex)

          self.topicCount = self.messageQuery.count_topic_search_keyword(
            self.searchTokens, self.siteInfo.get_id(), groupIds)

          self.totalNumTopics = self.messageQuery.count_topics()
          
          self.wordCounts = self.messageQuery.word_counts()

          tIds = [t['topic_id'] for t in self.topics]
          
          self.topicFiles = self.messageQuery.files_metata_topic(tIds)
          
          hashkey = sha.new('-'.join(tIds)+dbname).hexdigest()
          cTopicsWordCounts = self.cache_topicsWordCounts.get(hashkey)
          if cTopicsWordCounts and cTopicsWordCounts['postCount'] == postCount:
              self.topicsWordCounts = cTopicsWordCounts['object']
          else:
              self.topicsWordCounts = self.messageQuery.topics_word_count(tIds)
              cTopicsWordCounts = {'object': self.topicsWordCounts,
                                   'postCount': postCount}
              self.cache_topicsWordCounts.add(hashkey, cTopicsWordCounts)

      def render(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled

          pageTemplate = PageTemplateFile(self.pageTemplateFileName)
          r = pageTemplate(view=self)
         
          return r
          
      #########################################
      # Non standard methods below this point #
      #########################################
          
      def get_results(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled

          groupCache =  getattr(self.view, '__group_object_cache', {})
          authorCache = getattr(self.view, '__author_object_cache', {})
          
          for topic in self.topics:
              retval = topic
              
              authorInfo = authorCache.get(retval['last_post_user_id'], None)
              if not authorInfo:
                  authorInfo = createObject('groupserver.AuthorInfo', 
                    self.context, retval['last_post_user_id'])
                  authorCache[retval['last_post_user_id']] = authorInfo
              authorId = authorInfo.get_id()
              authorD = {
                'exists': authorInfo.exists(),
                'id': authorId,
                'name': authorInfo.get_realnames(),
                'url': authorInfo.get_url(),
                'only': self.view.only_author(authorId),
                'onlyURL': self.view.only_author_link(authorId)
              }
              retval['last_author'] = authorD

              groupInfo = groupCache.get(topic['group_id'], None)
              if not groupInfo:
                  groupInfo = createObject('groupserver.GroupInfo', 
                    self.context, topic['group_id'])
                  groupCache[topic['group_id']] = groupInfo
              groupD = {
                'id': groupInfo.get_id(),
                'name': groupInfo.get_name(),
                'url': groupInfo.get_url(),
                'only': self.view.only_group(groupInfo.get_id()),
                'onlyURL': self.view.only_group_link(groupInfo.get_id())
              }
              retval['group'] = groupD
              
              files = [{'name': f['file_name'],
                        'url': '/r/topic/%s#post-%s' % (f['post_id'], f['post_id']),
                        'icon': '/++resource++fileIcons/%s.png' % \
                          f['mime_type'].replace('/','-')
                       } for f in self.topicFiles 
                       if f['topic_id'] == topic['topic_id']]
                       
              retval['files'] = files
              
              kwds = self.get_keywords_for_topic(topic)
              retval['keywords'] = kwds
              wds = [w['word'] for w in kwds]
              retval['keywordSearch'] = self.get_keyword_search_link(wds)
              
              yield retval

      def get_keywords_for_topic(self, topic):
          tId = topic['topic_id']
          topicWords = [tw for tw in self.topicsWordCounts 
            if tw['topic_id'] == tId]
          twc = float(sum([w['count'] for w in topicWords]))
          wc = self.wordCounts
          words = [{'word':  w['word'],
                    'tfidf': (w['count']/twc)*\
                              math.log10(self.totalNumTopics/\
                                         float(wc.get('word', 1)))}
                    for w in topicWords
                    if ((len(w['word']) > 3) and 
                         (w['word'] not in STOP_WORDS))]
          words.sort(tfidf_sort)

          retval = words[:self.keywordLimit]          
          assert len(retval) <= self.keywordLimit
          return retval
          
      def show_previous(self):
          retval = (self.startIndex > 0)
          return retval
          
      def previous_link(self):
          retval = self.view.get_search_url(startIndex=self.previous_chunk())
          return retval
          
      def previous_chunk(self):
          retval = self.startIndex - self.limit
          if retval < 0:
              retval = 0
          assert retval >= 0
          return retval
          
      def show_next(self):
          retval = (self.topicCount >= (self.startIndex + self.limit))
          return retval
          
      def next_link(self):
          retval = self.view.get_search_url(startIndex=self.next_chunk())
          return retval

      def next_chunk(self):
          retval = self.startIndex + self.limit
          return retval
              
      def get_group_link(self, groupId):
          return self.view.only_group_link(groupId)

      def get_keyword_search_link(self, keywords):
          return self.view.get_search_url(searchText=keywords)

zope.component.provideAdapter(GSTopicResultsContentProvider,
    provides=zope.contentprovider.interfaces.IContentProvider,
    name="groupserver.TopicResults")

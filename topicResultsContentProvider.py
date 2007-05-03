import sys, re, datetime, time, types, string, math
import Products.Five, DateTime, Globals
import zope.schema
import zope.app.pagetemplate.viewpagetemplatefile
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
import zope.interface, zope.component, zope.publisher.interfaces
import zope.viewlet.interfaces, zope.contentprovider.interfaces 

from Products.PythonScripts.standard import html_quote
import DocumentTemplate

import Products.XWFMailingListManager.view
import Products.GSContent, Products.XWFCore.XWFUtils
from interfaces import IGSTopicResultsContentProvider
from queries import MessageQuery
from Products.GSContent.view import GSSiteInfo

class GSTopicResultsContentProvider(object):
      """GroupServer Topic Search-Results Content Provider
      """

      zope.interface.implements( IGSTopicResultsContentProvider )
      zope.component.adapts(zope.interface.Interface,
          zope.publisher.interfaces.browser.IDefaultBrowserLayer,
          zope.interface.Interface)
      
      def __init__(self, context, request, view):
          self.__parent__ = self.view = view
          self.__updated = False
      
          self.context = context
          self.request = request
          
      def update(self):
          self.__updated = True

          self.da = self.context.zsqlalchemy 
          assert self.da, 'No data-adaptor found'
          self.messageQuery = MessageQuery(self.context, self.da)
          self.siteInfo = GSSiteInfo(self.context)

          subjectTopics = self.subject_search(self.searchText)
          keywordTopics = self.keyword_search(self.searchText)
          allTopics = subjectTopics + keywordTopics
          self.topics = self.remove_duplicate_topics(allTopics)
          self.topics.sort(self.date_sort)
          self.topics = self.topics[:self.limit]
          
          self.totalNumTopics = self.messageQuery.count_topics()
          self.wordCounts = self.messageQuery.word_counts()
          #self.topics = self.keyword_subject_search(self.searchText)
          #self.get_keywords_for_topic(self.topics[0]['topic_id'])
          self.add_keywords_to_topics()
          
      def render(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled

          pageTemplate = PageTemplateFile(self.pageTemplateFileName)
          r = pageTemplate(topics=self.topics)
         
          return r
          
      #########################################
      # Non standard methods below this point #
      #########################################
      
      def subject_search(self, searchText):
          assert hasattr(self, 'messageQuery')
          assert self.messageQuery

          group_ids = self.get_visible_group_ids()
          siteId = self.siteInfo.get_id()
          topics = self.messageQuery.topic_search_subect(searchText, 
            siteId, group_ids, limit=self.limit)
          topics = self.add_group_names_to_topics(topics)
          return topics
      
      def keyword_search(self, keyword):
          group_ids = self.get_visible_group_ids()
          siteId = self.siteInfo.get_id()
          topics = self.messageQuery.topic_search_keyword(keyword,
            siteId, group_ids, limit=self.limit)
          topics = self.add_group_names_to_topics(topics)
          return topics

      def keyword_subject_search(self, keyword):
          group_ids = self.get_visible_group_ids()
          siteId = self.siteInfo.get_id()
          topics = self.messageQuery.topic_search_keyword_subject(keyword,
            siteId, group_ids, limit=self.limit)
          topics = self.add_group_names_to_topics(topics)
          return topics

          
      def add_group_names_to_topics(self, topics):
          ts = topics
          
          site_root = self.context.site_root()
          siteId = self.siteInfo.get_id()
          site = getattr(getattr(site_root, 'Content'), siteId)
          groupsObj = getattr(site, 'groups')

          for topic in ts:
              group = getattr(groupsObj, topic['group_id'])
              topic['group_name'] = group.title_or_id()
          return ts
      
      
      def get_visible_group_ids(self):
          site_root = self.context.site_root()
          siteId = self.view.siteInfo.get_id()
          site = getattr(getattr(site_root, 'Content'), siteId)
          groupsObj = getattr(site, 'groups')
          
          allGroups = groupsObj.objectValues(['Folder', 'Folder (Ordered)'])
          
          visibleGroups = []
          for group in allGroups:
              try:
                  group.messages.getId()
              except:
                  continue
              else:
                  visibleGroups.append(group)
          
          retval = [g.getId() for g in visibleGroups]
          return retval
          
      def date_sort(self, a, b):
          retval = 0
          if a['last_post_date'] < b['last_post_date']:
              retval = 1
          elif a['last_post_date'] == b['last_post_date']:
              retval = 0
          else:
              retval = -1

          return retval

      def remove_duplicate_topics(self, topics):
          ts = topics
          
          topicsSeen = []
          topicIDsSeen = []
          i = 1
          for topic in ts:
              if topic['topic_id'] not in topicIDsSeen:
                  topicsSeen.append(topic)
                  topicIDsSeen.append(topic['topic_id'])
          return topicsSeen
      
      def get_keywords_for_topic(self, topicId):
          words = self.messageQuery.topic_word_count(topicId)
          twc = float(sum([w['count'] for w in words]))
          wc = self.wordCounts
          words = [{'word':  w['word'],
                    'count': w['count'],
                    'tfidf': (w['count']/twc)*\
                              math.log10(self.totalNumTopics/\
                                         float(wc['word']))}
                    for w in words]
          words.sort(self.keywords_sort)
          return words
          
      def keywords_sort(self, a, b):
          if a['tfidf'] < b['tfidf']:
              retval = 1
          elif a['tfidf'] == b['tfidf']:
              retval = 0
          else:
              retval = -1
          return retval

      def add_keywords_to_topics(self):
          for topic in self.topics:
              keywords = self.get_keywords_for_topic(topic['topic_id'])
              topic['keywords'] = keywords[:6]
              
zope.component.provideAdapter(GSTopicResultsContentProvider,
    provides=zope.contentprovider.interfaces.IContentProvider,
    name="groupserver.TopicResults")

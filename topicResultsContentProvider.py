import sys, re, datetime, time, types, string, math
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

          self.topics = self.messageQuery.topic_search_keyword_subject(
            self.searchTokens.keywords, self.siteInfo.get_id(), 
            groupIds, limit=self.limit, offset=self.startIndex)
          assert len(self.topics) <= (self.limit * 2)
          
          self.topics = self.remove_non_existant_groups(self.topics)
          self.topics = self.add_group_names_to_topics(self.topics)
          
          self.totalNumTopics = self.messageQuery.count_topics()
          self.wordCounts = self.messageQuery.word_counts()
          self.add_words_to_topics()
                   
      def render(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled

          pageTemplate = PageTemplateFile(self.pageTemplateFileName)
          r = pageTemplate(view=self)
         
          return r
          
      #########################################
      # Non standard methods below this point #
      #########################################
          
      def add_group_names_to_topics(self, topics):
          ts = topics
          groupsObj = self.groupsInfo.groupsObj
          for topic in ts:
              if hasattr(groupsObj, topic['group_id']):
                  group = getattr(groupsObj, topic['group_id'])
                  topic['group_name'] = group.title_or_id()
          return ts

      def remove_non_existant_groups(self, topics):
          groupIds = self.groupsInfo.get_visible_group_ids()
          retval = [topic for topic in topics 
                    if (topic['group_id'] in groupIds)]
          
          return retval

      def get_keywords_for_topic(self, topic):
          twc = float(sum([w['count'] for w in topic['words']]))
          wc = self.wordCounts
          words = [{'word':  w['word'],
                    'tfidf': (w['count']/twc)*\
                              math.log10(self.totalNumTopics/\
                                         float(wc.get('word', 1)))}
                    for w in topic['words']
                    if ((len(w['word']) > 3) and 
                         (w['word'] not in STOP_WORDS))]
          words.sort(self.keywords_sort)

          retval = words[:self.keywordLimit]          
          assert len(retval) <= self.keywordLimit
          return retval
          
      def keywords_sort(self, a, b):
          if a['tfidf'] < b['tfidf']:
              retval = 1
          elif a['tfidf'] == b['tfidf']:
              retval = 0
          else:
              retval = -1
          return retval
      
      def add_words_to_topics(self):
          topicIds = [topic['topic_id'] for topic in self.topics]
          topicWords = self.messageQuery.topics_word_count(topicIds)
          for topic in self.topics:
              tid = topic['topic_id']
              words = [topicWord for topicWord in topicWords 
                       if(topicWord['topic_id']==tid)]
              topic['words'] = words          
         
      def get_results(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled
              
          for topic in self.topics:
              retval = topic
              retval['keywords'] = self.get_keywords_for_topic(retval)
              retval['show_group'] = (self.view.groupId != retval['group_id'])
              yield retval
              
      def get_group_link(self, groupId):
          return self.view.only_group_link(groupId)

      def get_keyword_search_link(self, keywords):
          return self.view.get_search_url(searchText=keywords)

zope.component.provideAdapter(GSTopicResultsContentProvider,
    provides=zope.contentprovider.interfaces.IContentProvider,
    name="groupserver.TopicResults")

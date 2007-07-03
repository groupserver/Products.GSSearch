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

          self.topicCount = self.messageQuery.count_topic_search_keyword_subject(
            self.searchTokens.keywords, self.siteInfo.get_id(), groupIds)
          
          self.totalNumTopics = self.messageQuery.count_topics()
          self.wordCounts = self.messageQuery.word_counts()
                   
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

          visibleGroupIds = self.groupsInfo.get_visible_group_ids()
              
          for topic in self.topics:
              if topic['group_id'] in visibleGroupIds:
                retval = topic

                groupInfo = createObject('groupserver.GroupInfo', 
                  self.context, topic['group_id'])
                groupD = {
                  'id': groupInfo.get_id(),
                  'name': groupInfo.get_name(),
                  'url': groupInfo.get_url(),
                  'only': self.view.only_group(groupInfo.get_id()),
                  'onlyURL': self.view.only_group_link(groupInfo.get_id())
                }
                retval['group'] = groupD
                
                kwds = self.get_keywords_for_topic(topic)
                retval['keywords'] = kwds
                wds = [w['word'] for w in kwds]
                retval['keywordSearch'] = self.get_keyword_search_link(wds)
                
                yield retval

      def get_keywords_for_topic(self, topic):
          topicWords = self.words_for_topic(topic['topic_id'])
          twc = float(sum([w['count'] for w in topicWords]))
          wc = self.wordCounts
          words = [{'word':  w['word'],
                    'tfidf': (w['count']/twc)*\
                              math.log10(self.totalNumTopics/\
                                         float(wc.get('word', 1)))}
                    for w in topicWords
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

      def words_for_topic(self, topicId):
          topicWords = self.messageQuery.topics_word_count([topicId])
          return topicWords
          
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

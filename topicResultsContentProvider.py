import sys, re, datetime, time, types, string, math
from sets import Set
import Products.Five, DateTime, Globals
import zope.schema
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
from Products.GSContent.view import GSSiteInfo
import visible_groups

# --=mpj17=-- I wonder if we can do something cleaver with viewlets and
#    the "yeild" statement, similar to how search is implemented in
#    von Weitershausen, P, "Web Component Development with Zope 3",
#      Springer, Berlin, 2007, pp369--371

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

          searchKeywords = self.searchText.split()
          
          self.groupIds = [gId for gId in self.groupIds if gId]
          if self.groupIds:
              groupIds = visible_groups.visible_groups(self.groupIds,
                self.context)
          else:
             groupIds = visible_groups.get_all_visible_groups(self.context)
                    
          t0 = time.time()

          subjectTopics = self.subject_search(searchKeywords, groupIds)
          keywordTopics = self.keyword_search(searchKeywords, groupIds)
          
          self.topics = subjectTopics + keywordTopics
          assert len(self.topics) <= (self.limit * 2)
          
          self.topics = self.remove_duplicate_topics(self.topics)
          self.topics = self.remove_non_existant_groups(self.topics)
          self.topics.sort(self.date_sort)
          self.topics = self.topics[:self.limit]
          
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
      
      def get_visible_group_ids(self):
          groupsObj = self.get_groups_object()
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

      def get_groups_object(self):
          site_root = self.context.site_root()
          siteId = self.siteInfo.get_id()
          site = getattr(getattr(site_root, 'Content'), siteId)
          groupsObj = getattr(site, 'groups')
          
          return groupsObj

      def subject_search(self, keywords, groupIds):
          assert hasattr(self, 'messageQuery')
          assert self.messageQuery

          siteId = self.siteInfo.get_id()
          topics = self.messageQuery.topic_search_subect(keywords, 
            siteId, groupIds, limit=self.limit, offset=self.startIndex)
          return topics
      
      def keyword_search(self, keywords, groupIds):
          if keywords:
              siteId = self.siteInfo.get_id()
              topics = self.messageQuery.topic_search_keyword(keywords,
                siteId, groupIds, limit=self.limit, offset=self.startIndex)
          else:
              topics = []
          return topics
          
      def add_group_names_to_topics(self, topics):
          ts = topics
          groupsObj = self.get_groups_object()
          for topic in ts:
              if hasattr(groupsObj, topic['group_id']):
                  group = getattr(groupsObj, topic['group_id'])
                  topic['group_name'] = group.title_or_id()
          return ts
                
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
          retval = []
          tIds = []
          for topic in topics:
              tId = topic['topic_id']
              if tId not in tIds:
                  tIds.append(tId)
                  retval.append(topic)
          return retval
          
      def remove_non_existant_groups(self, topics):
          groupIds = visible_groups.get_all_visible_groups(self.context)
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
              yield retval
              
zope.component.provideAdapter(GSTopicResultsContentProvider,
    provides=zope.contentprovider.interfaces.IContentProvider,
    name="groupserver.TopicResults")

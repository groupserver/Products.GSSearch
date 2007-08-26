import sys, re, datetime, time, types, string, math, sha, difflib, copy
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

def remove_plurals(tags):
    # --=mpj17=-- Warning, this modifies "tags" INPLACE
    for tag in copy.copy(tags):
        # find the closest match to the tag
        matches = difflib.get_close_matches(tag, tags, n=10, cutoff=0.85)
        if not matches:
            continue
        
        # find the shortest of the matches
        shortest = None
        for match in matches:
            if not shortest or len(match) <= len(shortest):
                shortest = match
        
        # remove the shortest match from the matches, then
        # clean up the original tags to remove all other matches
        matches.remove(shortest)
        for match in matches:
            tags.remove(match)
    
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
          
          dbname = self.da.getProperty('database')

          self.messageQuery = MessageQuery(self.context, self.da)

          self.siteInfo = createObject('groupserver.SiteInfo', 
            self.context)
          self.groupsInfo = createObject('groupserver.GroupsInfo', 
            self.context)
          self.searchTokens = createObject('groupserver.SearchTextTokens',
            self.s)
          
          self.groupIds = [gId for gId in self.gs if gId]
          if self.groupIds:
              groupIds = self.groupsInfo.filter_visible_group_ids(self.groupIds)
          else:
              groupIds = self.groupsInfo.get_visible_group_ids()
          
          topics = self.messageQuery.topic_search_keyword(
            self.searchTokens, self.siteInfo.get_id(), 
            groupIds, limit=self.l+1, offset=self.i)

          # important: we short circuit here because if we have no matching
          # topics several of the remaining queries are *very* intensive
          if not topics:
              self.moreTopics = False
              self.topics = []
              tIds = []
              self.topicFiles = []
              self.topicsWordCounts = []
          else:
              self.moreTopics = (len(topics) == (self.l + 1))
              self.topics = topics[:self.l]
              tIds = [t['topic_id'] for t in self.topics]
              self.topicFiles = self.messageQuery.files_metata_topic(tIds)
              self.topicsWordCounts = self.messageQuery.topics_word_count(tIds)

          self.totalNumTopics = self.messageQuery.count_topics()
          self.wordCounts = self.messageQuery.word_counts()

          hashkey = sha.new('-'.join(tIds)+dbname).hexdigest()
          postCount = self.messageQuery.count_posts()
          cTopicsWordCounts = {'object': self.topicsWordCounts,
                               'postCount': postCount}

      def render(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled

          pageTemplate = PageTemplateFile(self.pageTemplateFileName)
          onlyGroup = self.view.only_group(self)
          r = pageTemplate(view=self, onlyGroup=onlyGroup)
         
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
                'onlyURL': self.view.only_group_link(groupInfo.get_id())
              }
              retval['group'] = groupD
              retval['context'] = groupInfo.groupObj

              files = [{'name': f['file_name'],
                        'url': '/r/topic/%s#post-%s' % (f['post_id'], f['post_id']),
                        'icon': f['mime_type'].replace('/','-').replace('.','-'),
                       } for f in self.topicFiles 
                       if f['topic_id'] == topic['topic_id']]
                       
              retval['files'] = files
              
              kwds = self.get_keywords_for_topic(topic)
              wds = [w['word'] for w in kwds][:self.keywordLimit*3]
              remove_plurals(wds)
              wds = wds[:self.keywordLimit]
              retval['keywords'] = wds
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

          return words
          
      def show_previous(self):
          retval = (self.i > 0)
          return retval
          
      def previous_link(self):
          retval = self.view.get_search_url(startIndex=self.previous_chunk())
          return retval
          
      def previous_chunk(self):
          retval = self.i - self.l
          if retval < 0:
              retval = 0
          assert retval >= 0
          return retval
          
      def show_next(self):
          retval = self.moreTopics
          return retval
          
      def next_link(self):
          retval = self.view.get_search_url(startIndex=self.next_chunk())
          return retval

      def next_chunk(self):
          retval = self.i + self.l
          return retval
              
      def get_group_link(self, groupId):
          return self.view.only_group_link(groupId)

      def get_keyword_search_link(self, keywords):
          return self.view.get_search_url(searchText=keywords,
            startIndex=0)

zope.component.provideAdapter(GSTopicResultsContentProvider,
    provides=zope.contentprovider.interfaces.IContentProvider,
    name="groupserver.TopicResults")

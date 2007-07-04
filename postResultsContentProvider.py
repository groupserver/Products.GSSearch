import sys, re, datetime, time, types, string
import Products.Five, DateTime, Globals
import zope.schema
from zope.component import createObject
import zope.app.pagetemplate.viewpagetemplatefile
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
import zope.interface, zope.component, zope.publisher.interfaces
import zope.viewlet.interfaces, zope.contentprovider.interfaces 

import DocumentTemplate
import Products.XWFMailingListManager.view

import Products.GSContent, Products.XWFCore.XWFUtils

from interfaces import IGSPostResultsContentProvider
from queries import MessageQuery

class GSPostResultsContentProvider(object):
      """GroupServer Post Search-Results Content Provider
      """

      zope.interface.implements( IGSPostResultsContentProvider )
      zope.component.adapts(zope.interface.Interface,
          zope.publisher.interfaces.browser.IDefaultBrowserLayer,
          zope.interface.Interface)
      
      def __init__(self, context, request, view):
          self.__parent = view
          self.__updated = False
          self.context = context
          self.request = request
          self.view = view
          
          self.posts = []
          
      def update(self):
          self.__updated = True

          self.da = self.context.zsqlalchemy 
          assert self.da, 'No data-adaptor found'
          self.messageQuery = MessageQuery(self.context, self.da)
          # Both of the following should be aquired from adapters.
          self.siteInfo = createObject('groupserver.SiteInfo', 
            self.context)
          self.groupsInfo = createObject('groupserver.GroupsInfo', 
            self.context)

          self.searchTokens = createObject('groupserver.SearchTextTokens',
            self.searchText)
          
          self.groupIds = [gId for gId in self.groupIds if gId]
          if self.groupIds:
              self.groupIds = self.groupsInfo.filter_visible_group_ids(self.groupIds)
          else:
             self.groupIds = self.groupsInfo.get_visible_group_ids()

          self.posts = self.messageQuery.post_search_keyword(
            self.searchTokens, self.siteInfo.get_id(), self.groupIds, 
            self.authorIds, limit=self.limit, offset=self.startIndex)
            
          self.postCount = self.messageQuery.count_post_search_keyword(
            self.searchTokens, self.siteInfo.get_id(), self.groupIds, 
            self.authorIds)
            
      def render(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled
          pageTemplate = PageTemplateFile(self.pageTemplateFileName)
          r = pageTemplate(view=self)
          return r
          
      #########################################
      # Non standard methods below this point #
      #########################################
          
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
          assert self.posts
          retval = (self.postCount >= (self.startIndex + self.limit))
          return retval
          
      def next_link(self):
          retval = self.view.get_search_url(startIndex=self.next_chunk())
          return retval

      def next_chunk(self):
          retval = self.startIndex + self.limit
          return retval

      def get_results(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled

          authorCache = getattr(self.view, '__author_object_cache', {})
          groupCache =  getattr(self.view, '__group_object_cache', {})
          
          for post in self.posts:
              authorInfo = authorCache.get(post['user_id'], None)
              if not authorInfo:
                  authorInfo = createObject('groupserver.AuthorInfo', 
                    self.context, post['user_id'])
                  authorCache[post['user_id']] = authorInfo
              authorId = authorInfo.get_id()
              authorD = {
                'exists': authorInfo.exists(),
                'id': authorId,
                'name': authorInfo.get_realnames(),
                'url': authorInfo.get_url(),
                'only': self.view.only_author(authorId),
                'onlyURL': self.view.only_author_link(authorId)
              }
              
              groupInfo = groupCache.get(post['group_id'], None)
              if not groupInfo:
                  groupInfo = createObject('groupserver.GroupInfo', 
                    self.context, post['group_id'])
                  groupCache[post['group_id']] = groupInfo
              groupD = {
                'id': groupInfo.get_id(),
                'name': groupInfo.get_name(),
                'url': groupInfo.get_url(),
                'only': self.view.only_group(groupInfo.get_id()),
                'onlyURL': self.view.only_group_link(groupInfo.get_id())
              }
                  
              retval = {
                'postId': post['post_id'],
                'topicName': post['subject'],
                'author': authorD,
                'group': groupD,
                'date': post['date'],
                'timezone': 'foo',
                'postSummary': self.get_summary(post['body']),
              }
              yield retval

      def get_summary(self, text, nLines=1, lineLength=40):

          lines = text.split('\n')
          nonBlankLines = [l.strip() for l in lines if l and l.strip()]
          noQuoteLines = [l for l in nonBlankLines if l[0] != '>']
          multipleWordLines = [l for l in noQuoteLines 
            if len(l.split())>1]
            
          firstLine = multipleWordLines and multipleWordLines[0].lower() or ''
          if 'wrote' in firstLine:
              noWroteLines = multipleWordLines[1:]
          else:
              noWroteLines = multipleWordLines

          matchingLines = []          
          if self.searchText:
              matchingLines = [l for l in noWroteLines 
                               if reduce(lambda a, b: a or b, 
                                         map(lambda w: w in l.lower(),
                                             self.searchTokens.phrases))]
          if matchingLines:                               
              firstLines = matchingLines[:nLines]
              matchingSnippets = []
              for line in firstLines:
                  for w in self.searchTokens.phrases:
                      l = line.lower()
                      if w in l:
                          subLineLength = lineLength/2
                          start = l.index(w)
                          if start < subLineLength:
                              start = 0
                              end = lineLength
                          else:
                              start -= subLineLength
                              end = l.index(w) + subLineLength
                          s = line[start:end].strip()
                          if start != 0:
                              s = '&#8230;%s' % s
                          if end < len(l):
                              s = '%s&#8230;' % s
                          matchingSnippets.append(s )
              summary = '\n'.join(matchingSnippets)
          else:
              firstLines = noWroteLines[:nLines] 
              truncatedLines = []
              for l in firstLines:
                  if (len(l) > lineLength):
                      truncatedLines.append('%s&#8230;' % l[:lineLength])
                  else:
                      truncatedLines.append(l)
              summary = '\n'.join(truncatedLines)
          return summary
              
zope.component.provideAdapter(GSPostResultsContentProvider,
  provides=zope.contentprovider.interfaces.IContentProvider,
  name="groupserver.PostResults")


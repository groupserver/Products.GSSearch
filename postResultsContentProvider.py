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
              groupIds = self.groupsInfo.filter_visible_group_ids(self.groupIds)
          else:
             groupIds = self.groupsInfo.get_visible_group_ids()

          self.posts = self.posts_search(self.searchTokens.phrases, groupIds)

          
      def render(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled
          pageTemplate = PageTemplateFile(self.pageTemplateFileName)
          r = pageTemplate(view=self)
          return r
          
      #########################################
      # Non standard methods below this point #
      #########################################

      def posts_search(self, keywords, groupIds):
          assert hasattr(self, 'messageQuery')
          assert self.messageQuery
          siteId = self.siteInfo.get_id()
          posts = self.messageQuery.post_search_keyword(keywords, 
            siteId, groupIds, limit=self.limit, offset=self.startIndex)
          return posts

      def get_results(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled

          author_cache = getattr(self.view, '__author_object_cache', {})
              
          for post in self.posts:
              authorInfo = author_cache.get(post['user_id'], None)
              if not authorInfo:
                  authorInfo = createObject('groupserver.AuthorInfo', 
                    self.context, post['user_id'])
                  author_cache[post['user_id']] = authorInfo
                  
              authorD = {
                'exists': authorInfo.exists(),
                'id': authorInfo.get_id(),
                'name': authorInfo.get_realnames(),
                'url': authorInfo.get_url(),
              }
              
              groupInfo = createObject('groupserver.GroupInfo', 
                self.context, post['group_id'])

              groupD = {
                'id': groupInfo.get_id(),
                'name': groupInfo.get_name(),
                'url': groupInfo.get_url()
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
          firstLine = multipleWordLines[0].lower()
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

      # --=mpj17=-- The following few methods have been copied from 
      #     the post view in XWFMailingList. It really should be in
      #     a seperate class
      def user_authored(self):
          """Did the user write the email message?
          
          ARGUMENTS
              None.
          
          RETURNS
              A boolean that is "True" if the current user authored the
              email message, "False" otherwise.
              
          SIDE EFFECTS
              None.
              
          """
          user = self.request.AUTHENTICATED_USER
          retval = False
          if user.getId():
              retval = user.getId() == self.authorId
              
          assert retval in (True, False)
          return retval

      def get_author(self):
          """ Get the user object associated with the author.
          
          RETURNS
             The user object if the author has an account, otherwise None.
          
          """
          author_cache = getattr(self.view, '__author_object_cache', {})
          user = author_cache.get(self.authorId, None)
          if not user:
              user = get_user(self.context, self.authorId)
              author_cache[self.authorId] = user
              self.view.__author_object_cache = author_cache
              
          return user

      def author_exists(self):
          """ Does the author exist?
          
          """
          return self.get_author() and True or False
      
      def get_author_image(self):
          """Get the URL for the image of the post's author.
          
          RETURNS
             A string, representing the URL, if the author has an image,
             "None" otherwise.
             
          SIDE EFFECTS
             None.
          
          """
          user = self.get_author()
          retval = None
          if user:
              retval = user.get_image()
              
          return retval
           
      def get_author_realnames(self):
          """Get the names of the post's author.
          
          RETURNS
              The name of the post's author. 
          
          SIDE EFFECTS
             None.
          
          """
          retval = get_user_realnames( self.get_author(), self.authorId )
          
          return retval
          
zope.component.provideAdapter(GSPostResultsContentProvider,
                              provides=zope.contentprovider.interfaces.IContentProvider,
                              name="groupserver.PostResults")

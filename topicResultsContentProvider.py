import sys, re, datetime, time, types, string
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

          groups = self.get_visible_group_ids()
          self.topics = self.subject_search(self.searchText, 
              site_id=self.siteInfo.get_id(), group_ids=groups)
          
      def render(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled

          pageTemplate = PageTemplateFile(self.pageTemplateFileName)
          r = pageTemplate(topics=self.topics)
         
          return r
          
      #########################################
      # Non standard methods below this point #
      #########################################
      
      def subject_search(self, searchText, site_id, group_ids=[]):
          assert hasattr(self, 'messageQuery')
          assert self.messageQuery

          site_root = self.context.site_root()
          siteId = self.view.siteInfo.get_id()
          site = getattr(getattr(site_root, 'Content'), siteId)
          groupsObj = getattr(site, 'groups')

          topics = self.messageQuery.topic_search_subect(searchText, 
            site_id, group_ids)
            
          # Add a group-name to each topic
          for topic in topics:
              group = getattr(groupsObj, topic['group_id'])
              topic['group_name'] = group.title_or_id()
          return topics
          
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
          
zope.component.provideAdapter(GSTopicResultsContentProvider,
    provides=zope.contentprovider.interfaces.IContentProvider,
    name="groupserver.TopicResults")

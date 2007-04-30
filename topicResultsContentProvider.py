import sys, re, datetime, time, types, string
import Products.Five, DateTime, Globals
import zope.schema
import zope.app.pagetemplate.viewpagetemplatefile
import zope.pagetemplate.pagetemplatefile
import zope.interface, zope.component, zope.publisher.interfaces
import zope.viewlet.interfaces, zope.contentprovider.interfaces 

import DocumentTemplate
import Products.XWFMailingListManager.view

import Products.GSContent, Products.XWFCore.XWFUtils

from interfaces import IGSTopicResultsContentProvider
from queries import MessageQuery

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

          
      def render(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled
          retval = u'''<p>I am the topic results</p>
            <ul>
              <li>Search Text: %s</li>
            </ul>''' % self.searchText
          return retval
          
      #########################################
      # Non standard methods below this point #
      #########################################
      
      def subject_search(self, searchText):
          pass

zope.component.provideAdapter(GSTopicResultsContentProvider,
    provides=zope.contentprovider.interfaces.IContentProvider,
    name="groupserver.TopicResults")

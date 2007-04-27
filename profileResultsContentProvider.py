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

from interfaces import IGSProfileResultsContentProvider

class GSProfileResultsContentProvider(object):
      """GroupServer Profile Search-Results Content Provider
      """

      zope.interface.implements( IGSProfileResultsContentProvider )
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
          
      def render(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled
          retval = '<p>I am the profile results</p>'
          return retval
          
      #########################################
      # Non standard methods below this point #
      #########################################

zope.component.provideAdapter(GSProfileResultsContentProvider,
                              provides=zope.contentprovider.interfaces.IContentProvider,
                              name="groupserver.ProfileResults")

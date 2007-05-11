import sys, re, datetime, time, types, string
import Products.Five, DateTime, Globals
import zope.schema
import zope.app.pagetemplate.viewpagetemplatefile
import zope.pagetemplate.pagetemplatefile
import zope.interface, zope.component, zope.publisher.interfaces
import zope.viewlet.interfaces, zope.contentprovider.interfaces 
from zope.pagetemplate.pagetemplatefile import PageTemplateFile

import DocumentTemplate
import Products.XWFMailingListManager.view

import Products.GSContent, Products.XWFCore.XWFUtils

from interfaces import IGSFileResultsContentProvider

class GSFileResultsContentProvider(object):
      """GroupServer File Search-Results Content Provider
      """

      zope.interface.implements( IGSFileResultsContentProvider )
      zope.component.adapts(zope.interface.Interface,
          zope.publisher.interfaces.browser.IDefaultBrowserLayer,
          zope.interface.Interface)
      
      
      def __init__(self, context, request, view):
          self.__parent = view
          self.__updated = False
          self.context = context
          self.request = request
          self.view = view
          
          assert hasattr(self.context, 'Catalog'), 'Catalog cannot ' \
            "be found"
          self.catalog = self.context.Catalog
          self.results = []
          
      def update(self):
          self.__updated = True

          searchKeywords = self.searchText.split()
          self.results = self.search_site(searchKeywords)
          
          
      def render(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled

          pageTemplate = PageTemplateFile(self.pageTemplateFileName)
          r = pageTemplate(view=self)
         
          return r
          
      #########################################
      # Non standard methods below this point #
      #########################################
      
      def search_site(self, searchKeywords):
          # Mostly taken from SiteSearch/lscripts/search_site.py
                    
          results = self.catalog.searchResults(meta_type='XML Template',
            sort_order='decending', 
            indexable_content=' or '.join(searchKeywords),
            id='content_en')
          retval = []
          for result in results[:self.limit]:
              # Because the catalogue returns a week reference, getting
              #  the object may not always work
              try:
                  obj = result.getObject()
                  obj.title
                  retval.append(obj)
              except:
                  pass
          assert len(retval) <= self.limit, 'Too many results'
          return retval

      def get_results(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled
          for result in self.results:
              url = result.absolute_url().strip('content_en')

              owner = result.getOwner()
              if (('Manager' in owner.roles) 
                  or not hasattr(owner, 'getProperty')):
                  ownerName = 'the administrator'
              else:
                  ownerName = owner.getProperty('preferredName', 
                    'an unknown user')

              date = result.bobobase_modification_time
                            
              retval =  {
                'icon': '/++resource++fileIcons/text-xml.png',
                'title': result.title_or_id(),
                'date': date,
                'url': url,
                'user': ownerName
              }
              assert retval
              yield retval

zope.component.provideAdapter(GSFileResultsContentProvider,
                              provides=zope.contentprovider.interfaces.IContentProvider,
                              name="groupserver.FileResults")

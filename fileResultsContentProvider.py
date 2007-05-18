import sys, re, datetime, time, types, string
from sets import Set
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
from Products.GSContent.view import GSSiteInfo
from interfaces import IGSFileResultsContentProvider
import visible_groups

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

          self.siteInfo = GSSiteInfo(self.context)
          
          assert hasattr(self.context, 'Catalog'), 'Catalog cannot ' \
            "be found"
          self.catalog = self.context.Catalog
          self.results = []
          
      def update(self):
          self.__updated = True

          searchKeywords = self.searchText.split()

          self.groupIds = [gId for gId in self.groupIds if gId]
          if self.groupIds:
              groupIds = visible_groups.visible_groups(self.groupIds, 
                self.context)
          else:
             groupIds = visible_groups.get_all_visible_groups(self.context)
          
          self.results = self.search_files(searchKeywords, groupIds,
            self.searchPostedFiles, self.searchSiteFiles)
          
      def render(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled

          pageTemplate = PageTemplateFile(self.pageTemplateFileName)
          r = pageTemplate(view=self)
          
          return r
          
      #########################################
      # Non standard methods below this point #
      #########################################

      def search_files(self, searchKeywords, groupIds,
                       searchFileLibrary=True, searchWebPages=True):

          retval = []
          postedFiles = []
          siteFiles = []
          site_root = self.context.site_root()

          if searchFileLibrary:
              assert hasattr(site_root, 'FileLibrary2'), \
                'Cannot search: file library not found'
              fileLibrary = site_root.FileLibrary2
              fileLibraryPath = '/'.join(fileLibrary.getPhysicalPath())
              postedFiles = self.search_files_in_path(searchKeywords, 
                groupIds, fileLibraryPath, 'XWF File 2')
              postedFiles = [o for o in postedFiles if o]
              
          if searchWebPages:
              sitePath = self.siteInfo.get_path()
              siteFiles = self.search_files_in_path(searchKeywords, 
                path=sitePath, metaType='XML Template')
              siteFiles = [o for o in siteFiles if o]
              
          #r = [o for o in postedFiles + siteFiles if o]
          r = postedFiles + siteFiles
          r.sort(self.sort_file_results)
          s = []
          for o in r:
              try:
                  obj = o.getObject()
              except:
                  continue
              else:
                  if obj not in s:
                      s.append(obj)
                      
          retval = s[:self.limit]
          return retval
              
      def search_files_in_path(self, searchKeywords, groupIds=[], 
        path='', metaType=''):
          retval = []
          
          searchExpr = ' or '.join(searchKeywords)
          queries = [{'title': searchExpr}, 
                     {'indexable_content': searchExpr},
                     {'tags': searchExpr}]
          for q in queries:
              q['path'] = path

          catalog = self.context.Catalog
          results = []
          if groupIds:
              for query in queries:
                results += catalog(query, meta_type=metaType, 
                  group_ids=groupIds)
          else:
              for query in queries:
                  results += catalog(query, meta_type=metaType)
          return results
          
      def sort_file_results(self, a, b):
          if a.modification_time < b.modification_time:
              retval = 1
          elif a.modification_time == b.modification_time:
              retval = 0
          else:
              retval = -1
          return retval
          
      def get_results(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled
          for result in self.results:
              url = result.absolute_url().strip('content_en')

              owner = result.getOwner()
              if (owner and ('Manager' in owner.roles)
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

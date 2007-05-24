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
from Products.GSContent.interfaces import IGSSiteInfo, IGSGroupsInfo
from interfaces import IGSFileResultsContentProvider
from fileSearchResult import GSFileSearchResult
from queries import MessageQuery

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
                    
      def update(self):
          self.__updated = True

          self.da = self.context.zsqlalchemy 
          assert self.da, 'No data-adaptor found'
          self.messageQuery = MessageQuery(self.context, self.da)
          
          # Both of the following should be aquired from adapters.
          self.siteInfo = IGSSiteInfo(self.context)
          self.groups = IGSGroupsInfo(self.context)
         
          searchKeywords = self.searchText.split()

          assert hasattr(self.context, 'Catalog'), 'Catalog cannot ' \
            "be found"
          self.catalog = self.context.Catalog
          self.results = []
          
          self.groupIds = [gId for gId in self.groupIds if gId]
          if self.groupIds:
              groupIds = self.groups.filter_visible_group_ids(self.groupIds)
          else:
             groupIds = self.groups.get_visible_group_ids()
          
          self.results = self.search_files(searchKeywords, groupIds)
          self.results = self.remove_non_existant_groups(self.results)
          
          start = self.filesStartIndex
          end = self.filesStartIndex + self.filesLimit
          self.resultsCount = len(self.results)
          self.results = self.results[start : end]

          fIds = [r['id'] for r in self.results]
          self.filePostMap = self.get_post_ids_from_file_ids(fIds)
          
      def render(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled

          pageTemplate = PageTemplateFile(self.pageTemplateFileName)
          r = pageTemplate(view=self)
          
          return r
          
      #########################################
      # Non standard methods below this point #
      #########################################

      def search_files(self, searchKeywords, groupIds):

          retval = []
          postedFiles = []
          siteFiles = []
          site_root = self.context.site_root()

          assert hasattr(site_root, 'FileLibrary2'), \
            'Cannot search: file library not found'
          fileLibrary = site_root.FileLibrary2
          fileLibraryPath = '/'.join(fileLibrary.getPhysicalPath())
          postedFiles = self.search_files_in_path(searchKeywords, 
            groupIds, fileLibraryPath, 'XWF File 2')
          postedFiles = [o for o in postedFiles if o]
              
          postedFiles.sort(self.sort_file_results)
          fileIds = []
          retval = []
          for o in postedFiles:
              if o['id'] not in fileIds:
                  fileIds.append(o['id'])
                  retval.append(o)

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
                  r = catalog(query, meta_type=metaType, group_ids=groupIds)
                  results += r
                  
          else:
              for query in queries:
                  results += catalog(query, meta_type=metaType)
          return results
      
      def get_post_ids_from_file_ids(self, fileIds):
          retval = self.messageQuery.post_ids_from_file_ids(fileIds)
          return retval
      
      def sort_file_results(self, a, b):
          ta = a['modification_time']
          tb = b['modification_time']

          if ta < tb:
              retval = 1
          elif ta == tb:
              retval = 0
          else:
              retval = -1
          return retval

      def remove_non_existant_groups(self, files):
          # The reason that we do this is security: Bruce S. cannot
          #   add a group-id to the search-query and find out Alice and
          #   Bob's shared secret.
          groupIds = self.groups.get_visible_group_ids()
          retval = [f for f in files 
                    if (f['group_ids'][0] in groupIds)]   
          return retval
          
      def get_results(self):
          if not self.__updated:
              raise interfaces.UpdateNotCalled

          for result in self.results:
              r = GSFileSearchResult(self.view, self.context, result)
              
              retval =  {
                'icon': r.get_icon(),
                'title': r.get_title(),
                'tags': r.get_tags(),
                'date': r.get_date(),
                'url': r.get_url(),
                'owner_name': r.get_owner_name(),
                'owner_id': r.get_owner_id(),
                'group_id': r.get_group_info().get_id(),
                'group_name': r.get_group_info().get_name(),
                'group_url': r.get_group_info().get_url(),
                'post_id': self.filePostMap.get(r.get_id(), ''),
                'topic_name': r.get_topic_name(),
                'show_group': self.view.groupId != r.get_group_info().get_id(),
              }
              assert retval
              yield retval
            
      def show_next_link(self):
          retval = (self.filesStartIndex + self.filesLimit) < self.resultsCount 
          return retval
      
      def get_next_link(self):
          fs = self.filesStartIndex
          fl = self.filesLimit
          return self.view.get_search_url(filesStartIndex=fs+fl)
          
zope.component.provideAdapter(GSFileResultsContentProvider,
                              provides=zope.contentprovider.interfaces.IContentProvider,
                              name="groupserver.FileResults")

# coding=utf-8
import sys, re, datetime, time, types, string
from sets import Set
import Products.Five, DateTime, Globals
import zope.schema
import zope.app.pagetemplate.viewpagetemplatefile
from zope.component import createObject
import zope.pagetemplate.pagetemplatefile
import zope.interface, zope.component, zope.publisher.interfaces
import zope.viewlet.interfaces, zope.contentprovider.interfaces 
from zope.pagetemplate.pagetemplatefile import PageTemplateFile

import DocumentTemplate
import Products.XWFMailingListManager.view

import Products.GSContent, Products.XWFCore.XWFUtils
from gs.groups.interfaces import IGSGroupsInfo
from Products.CustomUserFolder.interfaces import IGSUserInfo
from Products.ZCTextIndex.ParseTree import ParseError
from interfaces import IGSFileResultsContentProvider
from fileSearchResult import GSFileSearchResult
from queries import MessageQuery

import logging
logger = logging.getLogger('GSSearch')

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
        self.groups = IGSGroupsInfo(self.context)
        
        searchKeywords = self.s.split()

        assert hasattr(self.context, 'Catalog'), 'Catalog cannot ' \
        "be found"
        self.catalog = self.context.Catalog
        self.results = []
        
        groupIds = [gId for gId in self.gs if gId]
        if groupIds:
            groupIds = self.groups.filter_visible_group_ids(self.gs)
        
        # if group Ids are not specified now, populate with visible ones
        else:
            groupIds = self.groups.get_visible_group_ids()
        
        #--=mpj17=--Site ID!
        if groupIds:
            self.results = self.search_files(searchKeywords, groupIds, 
                self.a, self.ms) # TODO: Site ID
        else:
            self.results = []

        start = self.i
        end = start + self.l
        self.resultsCount = len(self.results)
        self.results = self.results[start : end]

        fIds = [r['id'] for r in self.results]
        self.filePostMap = self.get_post_ids_from_file_ids(fIds)
        
    def render(self):
        if not self.__updated:
            raise interfaces.UpdateNotCalled
        
        if self.results:
            pageTemplate = PageTemplateFile(self.pageTemplateFileName)
            r = pageTemplate(view=self)
        else:
            r = '<p id="file-search-none">No files found.</p>'
        
        return r
        
    #########################################
    # Non standard methods below this point #
    #########################################

    def search_files(self, searchKeywords, groupIds,
        authorIds, mimeTypes):#--=mpj17=--TODO: Site ID!

        logger.info("Performing search for %s, groups %s, authors %s" %
                    (searchKeywords, groupIds, authorIds))

        retval = []
        postedFiles = []
        siteFiles = []
        site_root = self.context.site_root()

        assert hasattr(site_root, 'FileLibrary2'), \
        'Cannot search: file library not found'
        fileLibrary = site_root.FileLibrary2
        fileLibraryPath = '/'.join(fileLibrary.getPhysicalPath())
        postedFiles = self.search_files_in_path(searchKeywords, 
            groupIds, fileLibraryPath, 'XWF File 2',
            authorIds, mimeTypes) #--=mpj17=-- TODO: Site ID!
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
    path='', metaType='', authorIds=[], mimeTypes=[]): #--=mpj17=-- TODO: Site ID!
        catalog = self.context.Catalog
        results = []
        
        # if we don't have any groupIds, don't perform any search, since
        # we will effectively end up filtering out all the results
        if groupIds:
            searchExpr = ' and '.join(searchKeywords)
            queries = [{'meta_text': searchExpr, 'path': path},
                        {'indexable_content': searchExpr, 'path': path}]
            if authorIds:
                authors = ' and '.join(authorIds)
            if mimeTypes:
                mimeQuery = ' and '.join(mimeTypes)
            for query in queries:
                query['meta_type'] = metaType
                query['group_ids'] = groupIds #TODO: Site ID!
                if authorIds:
                    query['dc_creator'] = authors
                if mimeTypes:
                    query['content_type'] = mimeQuery

                for k in query.keys():
                  if not query[k]:
                    del(query[k])
                try:
                    # we do unrestricted searches, since we're
                    # handling the security
                    r = catalog.unrestrictedSearchResults(None, **query)
                except ParseError, e:
                    if len(searchKeywords) == 1:
                        results = []
                        break
                    else:
                        r = []
                results += r
                        
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

    def get_results(self):
        if not self.__updated:
            raise interfaces.UpdateNotCalled

        groupCache =  getattr(self.view, '__group_object_cache', {})
        authorCache = getattr(self.view, '__author_object_cache', {})

        for result in self.results:
            r = GSFileSearchResult(self.view, self.context, result)
            
            authorInfo = authorCache.get(r.get_owner_id(), None)
            if not authorInfo:
                authorInfo = createObject('groupserver.UserFromId', 
                self.context, r.get_owner_id())
                authorCache[r.get_owner_id()] = authorInfo
            authorId = authorInfo.id
            authorD = {
            'id': authorInfo.id,
            'exists': not authorInfo.anonymous,
            'url': authorInfo.url,
            'name': authorInfo.name,
            'only': self.view.only_author(authorId),
            'onlyURL': self.view.only_author_link(authorId)
            }

            groupInfo = groupCache.get(r.get_group_info().get_id(), None)
            if not groupInfo:
                groupInfo = createObject('groupserver.GroupInfo', 
                self.context, r.get_group_info().get_id())
                groupCache[r.get_group_info().get_id()] = groupInfo
            groupD = {
            'id': groupInfo.get_id(),
            'name': groupInfo.get_name(),
            'url': groupInfo.get_url(),
            'only': self.view.only_group(groupInfo.get_id()),
            'onlyURL': self.view.only_group_link(groupInfo.get_id())
            }
            
            tags = ' '.join(r.get_tags())
            tagSearch = self.view.get_search_url(searchText=tags)
            
            postId = self.filePostMap.get(r.get_id(), '')
            fileURL = '/r/file/%s' % r.get_id()
            
            fileD = {'id': r.get_id(),
                'file': fileURL,
                'type': r.get_type(),
                'size': r.get_size(),
                'title': r.get_title(),
                'tags': r.get_tags(),
                'tag_search': tagSearch,
                'date': r.get_date(),
                'rfc3339_date': r.rfc3339_date,
                'url': r.get_url(),
                'thumbnail_url': r.thumbnail_url,}
            
            topicURL = '/r/topic/%s' % postId
            topicD = {
            'name': r.get_topic_name(),
            'url': topicURL,
            }

            postURL = '/r/post/%s' % postId
            postD = {
            'id': postId,
            'url': postURL,
            }              

            retval =  {
            'file': fileD,
            'group': groupD,
            'author': authorD,
            'post': postD,
            'topic': topicD,
            'context': self.context
            }
            assert retval
            yield retval
    
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
        retval = self.next_chunk() < self.resultsCount 
        return retval
    
    def next_link(self):
        retval = self.view.get_search_url(startIndex=self.next_chunk())
        return retval

    def next_chunk(self):
        retval = self.i + self.l
        return retval
          
zope.component.provideAdapter(GSFileResultsContentProvider,
                              provides=zope.contentprovider.interfaces.IContentProvider,
                              name="groupserver.FileResults")

# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright © 2012, 2013, 2014 OnlineGroups.net and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
from __future__ import absolute_import, unicode_literals
from zope.component import adapts, createObject, provideAdapter
from zope.contentprovider.interfaces import UpdateNotCalled, IContentProvider
from zope.interface import implements, Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from AccessControl import getSecurityManager
from Products.ZCTextIndex.ParseTree import ParseError
from gs.core import to_ascii
from gs.groups.interfaces import IGSGroupsInfo
from .interfaces import IGSFileResultsContentProvider
from .fileSearchResult import GSFileSearchResult
from .queries import MessageQuery

import logging
log = logging.getLogger('GSSearch')


class GSFileResultsContentProvider(object):
    """GroupServer File Search-Results Content Provider"""

    implements(IGSFileResultsContentProvider)
    adapts(Interface, IDefaultBrowserLayer, Interface)

    def __init__(self, context, request, view):
        self.__parent = view
        self.__updated = False
        self.context = context
        self.request = request
        self.view = view

    def update(self):
        self.__updated = True

        self.messageQuery = MessageQuery(self.context)

        # Both of the following should be acquired from adapters.
        self.groupsInfo = IGSGroupsInfo(self.context)

        user = getSecurityManager().getUser()

        searchKeywords = self.s.split()

        assert hasattr(self.context, 'Catalog'), 'Catalog cannot ' \
        "be found"
        self.catalog = self.context.Catalog
        self.results = []

        groupIds = [gId for gId in self.g if gId]

        memberGroupIds = []
        if self.mg and user.getId():
            memberGroupIds = [g.getId() for g in
                        self.groupsInfo.get_member_groups_for_user(user, user)]

        if groupIds:
            if memberGroupIds:
                groupIds = [gId for gId in self.groupIds
                                if gId in memberGroupIds]
            else:
                groupIds = self.groupsInfo.filter_visible_group_ids(groupIds)
        else:
            if memberGroupIds:
                groupIds = memberGroupIds
            else:
                groupIds = self.groupsInfo.get_visible_group_ids()

        #--=mpj17=--Site ID!
        if groupIds:
            self.results = self.search_files(searchKeywords, groupIds,
                self.a, self.m)  # TODO: Site ID
        else:
            self.results = []

        start = self.i
        end = start + self.l
        self.resultsCount = len(self.results)
        self.results = self.results[start: end]

        fIds = [r['id'] for r in self.results]
        self.filePostMap = self.get_post_ids_from_file_ids(fIds)

    def render(self):
        if not self.__updated:
            raise UpdateNotCalled()

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
        authorIds, mimeTypes):  # --=mpj17=--TODO: Site ID!

        log.debug("Performing search for %s, groups %s, authors %s" %
                    (searchKeywords, groupIds, authorIds))

        site_root = self.context.site_root()

        assert hasattr(site_root, 'FileLibrary2'), \
        'Cannot search: file library not found'
        fileLibrary = site_root.FileLibrary2
        # --=mpj17=-- Without this to_ascii call I get
        #    ValueError: invalid literal for int() with base 10: 's'
        # Ask me not why.
        fileLibraryPath = to_ascii('/'.join(fileLibrary.getPhysicalPath()))
        postedFiles = self.search_files_in_path(searchKeywords,
            groupIds, fileLibraryPath, 'XWF File 2',
            authorIds, mimeTypes)  # --=mpj17=-- TODO: Site ID!
        postedFiles = [o for o in postedFiles if o]

        postedFiles.sort(self.sort_file_results)
        fileIds = []
        retval = []
        for o in postedFiles:
            if o['id'] not in fileIds:
                fileIds.append(o['id'])
                retval.append(o)
        return retval

    def search_files_in_path(self, searchKeywords, groupIds=None,
        path='', metaType='', authorIds=None, mimeTypes=None):
        #--=mpj17=-- FIXME: Site ID!
        if groupIds is None:
            groupIds = []
        if authorIds is None:
            authorIds = []
        if mimeTypes is None:
            mimeTypes = []

        catalog = self.context.Catalog
        results = []

        # if we don't have any groupIds, don't perform any search, since
        # we will effectively end up filtering out all the results
        if groupIds:
            searchExpr = ' and '.join(searchKeywords)
            queries = [{'meta_text': searchExpr, 'path': path},
                        {'indexable_content': searchExpr, 'path': path}]

            for query in queries:
                query['meta_type'] = metaType
                query['group_ids'] = groupIds  # TODO: Site ID!
                if authorIds:
                    query['dc_creator'] = authorIds
                if mimeTypes:
                    query['content_type'] = mimeTypes

                cleanQuery = self.sanatise_query(query)
                try:
                    # we do unrestricted searches, since we're
                    # handling the security
                    r = catalog.unrestrictedSearchResults(None, **cleanQuery)
                except ParseError:
                    log.exception("Error while parsing search keywords:")
                    if len(searchKeywords) == 1:
                        results = []
                        break
                    else:
                        r = []
                results += r
        return results

    def sanatise_query(self, q):
        if not isinstance(q, dict):
            raise TypeError('Query is a {0}, not a dict'.format(type(q)))
        retval = {}
        for k in q:
            if q[k]:
                retval[k] = q[k]
        assert type(retval) == dict
        return retval

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
            raise UpdateNotCalled()

        groupCache = getattr(self.view, '__group_object_cache', {})
        authorCache = getattr(self.view, '__author_object_cache', {})

        for result in self.results:
            r = GSFileSearchResult(self.view, self.context, result)
            postId = self.filePostMap.get(r.get_id(), '')

            authorInfo = authorCache.get(r.get_owner_id(), None)
            if not authorInfo:
                authorInfo = createObject('groupserver.UserFromId',
                self.context, r.get_owner_id())
                authorCache[r.get_owner_id()] = authorInfo
            authorId = authorInfo.id
            only = False
            if self.view.author_count() == 1:
                only = True
            authorD = {
            'id': authorInfo.id,
            'exists': not authorInfo.anonymous,
            'url': authorInfo.url,
            'name': authorInfo.name,
            'only': only,
            'onlyURL': self.view.only_author_link(authorId)
            }

            groupInfo = groupCache.get(r.get_group_info().get_id(), None)
            if not groupInfo:
                groupInfo = createObject('groupserver.GroupInfo',
                self.context, r.get_group_info().get_id())
                groupCache[r.get_group_info().get_id()] = groupInfo
            group_count = self.view.group_count()

            only_group = False
            if group_count == 1:
                only_group = True

            groupD = {
            'id': groupInfo.get_id(),
            'name': groupInfo.get_name(),
            'url': groupInfo.get_url(),
            'only': only_group,
            'onlyURL': self.view.only_group_link(groupInfo.get_id())
            }

            tags = ' '.join(r.get_tags())
            tagSearch = self.view.get_search_url(searchText=tags)

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
                'thumbnail_url': r.thumbnail_url, }

            topicURL = '/groups/{0}/messages/topic/{1}'.format(groupInfo.id,
                                                               postId)
            topicD = {
            'name': r.get_topic_name(),
            'url': topicURL,
            }

            postURL = '/r/post/%s' % postId
            postD = {
            'id': postId,
            'url': postURL,
            }

            retval = {
            'file': fileD,
            'group': groupD,
            'author': authorD,
            'post': postD,
            'topic': topicD,
            'context': self.context
            }
            assert retval
            if postId:  # --=mpj17=-- Skips hidden posts
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

provideAdapter(GSFileResultsContentProvider, provides=IContentProvider,
                  name="groupserver.FileResults")

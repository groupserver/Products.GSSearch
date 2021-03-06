# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright © 2012, 2013, 2014, 2015 OnlineGroups.net and Contributors.
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
from __future__ import absolute_import, unicode_literals, print_function
from logging import getLogger
log = getLogger('GSSearch')
from sqlalchemy.exc import SQLAlchemyError
from zope.component import createObject
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from zope.interface import implementer, Interface
from zope.component import adapter, provideAdapter
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.contentprovider.interfaces import IContentProvider, UpdateNotCalled
import AccessControl
from gs.group.messages.text import split_message
from .interfaces import IGSPostResultsContentProvider
from .queries import MessageQuery


@implementer(IGSPostResultsContentProvider)
@adapter(Interface, IDefaultBrowserLayer, Interface)
class GSPostResultsContentProvider(object):
    """GroupServer Post Search-Results Content Provider"""
    def __init__(self, context, request, view):
        self.__parent = view
        self.__updated = False
        self.__searchFailed = True
        self.context = context
        self.request = request
        self.view = view
        self.posts = []

    def update(self):
        self.__updated = True
        self.messageQuery = MessageQuery(self.context)
        # Both of the following should be aquired from adapters.
        self.siteInfo = createObject('groupserver.SiteInfo', self.context)
        self.groupsInfo = createObject('groupserver.GroupsInfo', self.context)

        user = AccessControl.getSecurityManager().getUser()

        self.searchTokens = createObject('groupserver.SearchTextTokens', self.s)

        self.groupIds = [gId for gId in self.g if gId]

        memberGroupIds = []
        if self.mg and user.getId():
            memberGroupIds = [g.getId() for g in
                              self.groupsInfo.get_member_groups_for_user(user, user)]

        if self.groupIds:
            if memberGroupIds:
                self.groupIds = [gId for gId in self.groupIds if gId in memberGroupIds]
            else:
                self.groupIds = \
                    self.groupsInfo.filter_visible_group_ids(self.groupIds)
        else:
            if memberGroupIds:
                self.groupIds = memberGroupIds
            else:
                self.groupIds = self.groupsInfo.get_visible_group_ids()

        try:
            posts = self.messageQuery.post_search_keyword(
                self.searchTokens, self.siteInfo.get_id(), self.groupIds,
                self.a, limit=self.l + 1, offset=self.i)
        except SQLAlchemyError:
            log.exception("A problem occurred with a messageQuery:")
            self.__searchFailed = True
            return
        else:
            self.__searchFailed = False

        self.morePosts = (len(posts) == (self.l + 1))
        self.posts = posts[:self.l]

    def render(self):
        if self.__searchFailed:
            r = '''<div class="error" id="post-search-timeout">
                <p><strong>Posts Failed to Load</strong></p>
                <p>Sorry, the posts failed to load, because the server
                  took too long to respond.
                  <em>Please try again later.</em>
                </p>
              </div>'''
        else:
            if not self.__updated:
                raise UpdateNotCalled()
            pageTemplate = PageTemplateFile(self.pageTemplateFileName)

            onlyGroup = False
            if self.view.group_count() == 1:
                onlyGroup = self.view.group_count()

            onlyAuthor = False
            if self.view.author_count() == 1:
                onlyAuthor = self.view.author_count()

            if self.posts:
                r = pageTemplate(view=self, onlyGroup=onlyGroup, onlyAuthor=onlyAuthor)
            else:
                r = '<p id="post-search-none">No posts found.</p>'
        return r

    #########################################
    # Non standard methods below this point #
    #########################################

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
        retval = self.morePosts
        return retval

    def next_link(self):
        retval = self.view.get_search_url(startIndex=self.next_chunk())
        return retval

    def next_chunk(self):
        retval = self.i + self.l
        return retval

    def get_results(self):
        if not self.__updated:
            raise UpdateNotCalled()

        authorCache = getattr(self.view, '__author_object_cache', {})
        groupCache = getattr(self.view, '__group_object_cache', {})
        siteURL = self.siteInfo.get_url()

        for post in self.posts:
            authorInfo = authorCache.get(post['user_id'], None)
            if not authorInfo:
                authorInfo = createObject('groupserver.UserFromId', self.context, post['user_id'])
                authorCache[post['user_id']] = authorInfo
            authorId = authorInfo.id
            authorD = {
                'id': authorInfo.id,
                'exists': not authorInfo.anonymous,
                'url': authorInfo.url,
                'name': authorInfo.name,
                'onlyURL': self.view.only_author_link(authorId),
            }

            groupInfo = groupCache.get(post['group_id'], None)
            if not groupInfo:
                groupInfo = createObject('groupserver.GroupInfo', self.context, post['group_id'])
                groupCache[post['group_id']] = groupInfo
            groupD = {
                'id': groupInfo.get_id(),
                'name': groupInfo.get_name(),
                'url': groupInfo.relativeURL,
                'onlyURL': self.view.only_group_link(groupInfo.get_id()),
            }
            retval = {
                'context': groupInfo.groupObj,
                'postId': post['post_id'],
                'postURL': '%s/r/post/%s' % (siteURL, post['post_id']),
                'topicName': post['subject'],
                'author': authorD,
                'group': groupD,
                'date': post['date'],
                'timezone': 'foo',
                'postSummary': self.get_summary(post['body']),
                'postBody': post['body'],
                'postIntro': split_message(post['body']).intro,
                'files': post['files_metadata'],
            }
            yield retval

    def get_summary(self, text, nLines=1, lineLength=38):

        lines = text.split('\n')
        nonBlankLines = [l.strip() for l in lines if l and l.strip()]
        noQuoteLines = [l for l in nonBlankLines if l[0] != '>']
        multipleWordLines = [l for l in noQuoteLines if len(l.split()) > 1]

        firstLine = multipleWordLines and multipleWordLines[0].lower() or ''
        if 'wrote' in firstLine:
            noWroteLines = multipleWordLines[1:]
        else:
            noWroteLines = multipleWordLines

        matchingLines = []
        if self.s:
            matchingLines = [l for l in noWroteLines
                             if reduce(lambda a, b: a or b, map(lambda w: w in l.lower(),
                                       self.searchTokens.phrases), False)]
        if matchingLines:
            firstLines = matchingLines[:nLines]
            matchingSnippets = []
            for line in firstLines:
                for w in self.searchTokens.phrases:
                    l = line.lower()
                    if w in l:
                        subLineLength = lineLength / 2
                        start = l.index(w)
                        if start < subLineLength:
                            start = 0
                            end = lineLength
                        else:
                            start -= subLineLength
                            end = l.index(w) + subLineLength
                        s = line[start:end].strip()
                        if start != 0:
                            s = '\u2026%s' % s
                        if end < len(l):
                            s = '%s\u2026' % s
                        matchingSnippets.append(s)
            summary = '\n'.join(matchingSnippets)
        else:
            firstLines = noWroteLines[:nLines]
            truncatedLines = []
            for l in firstLines:
                if (len(l) > lineLength):
                    truncatedLines.append('%s\u2026' % l[:lineLength])
                else:
                    truncatedLines.append(l)
            summary = '\n'.join(truncatedLines)
        return summary

provideAdapter(GSPostResultsContentProvider, provides=IContentProvider,
               name="groupserver.PostResults")

# coding=utf-8
from __future__ import absolute_import, unicode_literals
from sqlalchemy.exc import SQLAlchemyError
from zope.component import createObject, adapts, provideAdapter
from zope.contentprovider.interfaces import IContentProvider, UpdateNotCalled
from zope.interface import implements, Interface
from zope.pagetemplate.pagetemplatefile import PageTemplateFile
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from gs.viewlet.contentprovider import SiteContentProvider
from Products.XWFCore.XWFUtils import get_the_actual_instance_from_zope
from .interfaces import IGSTopicResultsContentProvider
from .queries import MessageQuery

import logging
log = logging.getLogger('GSSearch')


class GSTopicResultsContentProvider(SiteContentProvider):
    """GroupServer Topic Search-Results Content Provider.

    """

    implements(IGSTopicResultsContentProvider)
    adapts(Interface, IDefaultBrowserLayer, Interface)

    def __init__(self, context, request, view):
        SiteContentProvider.__init__(self, context, request, view)

    def update(self):
        self.__updated = True

        self.messageQuery = MessageQuery(self.context)
        ctx = get_the_actual_instance_from_zope(self.view.context)
        self.groupsInfo = createObject('groupserver.GroupsInfo', ctx)
        self.searchTokens = createObject('groupserver.SearchTextTokens',
                                self.s)

        groupIds = [gId for gId in self.g if gId]

        user = self.loggedInUser.user
        memberGroupIds = []
        if self.mg and user.getId():
            mg = self.groupsInfo.get_member_groups_for_user(user, user)
            memberGroupIds = [g.getId() for g in mg]

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

        try:
            topics = self.messageQuery.topic_search_keyword(
                          self.searchTokens, self.siteInfo.get_id(),
                          groupIds, limit=self.l + 1, offset=self.i)
        except SQLAlchemyError:
            log.exception("A problem occurred with a message query:")
            self.__searchFailed = True
            return
        else:
            self.__searchFailed = False
        # important: we short circuit here because if we have no matching
        # topics several of the remaining queries are *very* intensive
        if not topics:
            self.moreTopics = False
            self.topics = []
            tIds = []
            self.topicFiles = []
            self.topicsWordCounts = []
        else:
            self.moreTopics = (len(topics) == (self.l + 1))
            self.topics = topics[:self.l]
            tIds = [t['topic_id'] for t in self.topics]
            self.topicFiles = self.messageQuery.files_metadata_topic(tIds)

    def render(self):
        if not self.__updated:
            raise UpdateNotCalled

        if self.__searchFailed:
            r = '''<div class="error" id="topic-serch-timeout">
                  <p><strong>Topics Failed to Load</strong></p>
                  <p>Sorry, the topics failed to load, because the server
                    took too long to respond.
                    <em>Please try again later.</em>
                  </p>
                </div>'''
        else:
            pageTemplate = PageTemplateFile(self.pageTemplateFileName)
            group_count = self.view.group_count()
            if group_count == 1:
                onlyGroup = True
            else:
                onlyGroup = False
            if self.topics:
                r = pageTemplate(view=self, onlyGroup=onlyGroup)
            else:
                r = '<p id="topic-search-none">No topics found.</p>'
        return r

    #########################################
    # Non standard methods below this point #
    #########################################

    def get_results(self):
        groupCache = getattr(self.view, '__group_object_cache', {})
        authorCache = getattr(self.view, '__author_object_cache', {})

        for topic in self.topics:
            retval = topic

            authorInfo = authorCache.get(retval['last_post_user_id'], None)
            if not authorInfo:
                authorInfo = createObject('groupserver.UserFromId',
                  self.context, retval['last_post_user_id'])
                authorCache[retval['last_post_user_id']] = authorInfo
            authorId = authorInfo.id
            authorD = {
                'id': authorInfo.id,
                'exists': not authorInfo.anonymous,
                'url': authorInfo.url,
                'name': authorInfo.name,
                'onlyURL': self.view.only_author_link(authorId)
            }
            retval['last_author'] = authorD

            groupInfo = groupCache.get(topic['group_id'], None)
            if not groupInfo:
                groupInfo = createObject('groupserver.GroupInfo',
                  self.context, topic['group_id'])
                groupCache[topic['group_id']] = groupInfo
            groupD = {
                'id': groupInfo.id,
                'name': groupInfo.name,
                'url': groupInfo.relativeURL,
                'onlyURL': self.view.only_group_link(groupInfo.get_id())
            }
            retval['group'] = groupD
            retval['context'] = groupInfo.groupObj

            files = [{'name': f['file_name'],
                        'url':
                          '/r/topic/%s#post-%s' % (f['post_id'], f['post_id']),
                        'icon':
                          f['mime_type'].replace('/', '-').replace('.', '-'),
                       } for f in self.topicFiles
                       if f['topic_id'] == topic['topic_id']]
            retval['files'] = files

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
        retval = self.moreTopics
        return retval

    def next_link(self):
        retval = self.view.get_search_url(startIndex=self.next_chunk())
        return retval

    def next_chunk(self):
        retval = self.i + self.l
        return retval

    def get_group_link(self, groupId):
        return self.view.only_group_link(groupId)

    def get_keyword_search_link(self, keywords):
        return self.view.get_search_url(searchText=keywords,
          startIndex=0)

provideAdapter(GSTopicResultsContentProvider,
    provides=IContentProvider,
    name="groupserver.TopicResults")

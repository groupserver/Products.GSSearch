# coding=utf-8

from App.class_init import InitializeClass

from zope.component import createObject
from zope.interface import implements
from Products.Five import BrowserView
from Products.PythonScripts.standard import url_quote

from interfaces import IGSSearchResults
from queries import MessageQuery


class GSSearchView(BrowserView):

    implements( IGSSearchResults )
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.siteInfo = createObject('groupserver.SiteInfo', context)
        
        self.searchText = self.request.get('s', '')
        if isinstance(self.searchText, list):
            self.searchText = ' '.join(self.searchText).strip()
        self.searchTokens = createObject('groupserver.SearchTextTokens', 
            self.searchText)
        
        self.memberGroupsOnly = self.request.get('mg', False) or False
        
        self.groupIds = self.request.get('g', None) or []
        if not isinstance(self.groupIds, list):
            self.groupIds = [self.groupIds]
        
        assert isinstance(self.groupIds, list), "groupIds were not in a list: %s" % self.groupIds
        self.groupIds = filter(None, self.groupIds)
        
        self.authorIds = self.request.get('a', []) or []
        if not isinstance(self.authorIds, list):
            self.authorIds = [self.authorIds]
        
        assert isinstance(self.authorIds, list), "authorIds were not in a list: %s" % self.authorIds
        self.authorIds = filter(None, self.authorIds)
        
        self.mimeTypes = self.request.get('m', []) or []
        if not isinstance(self.mimeTypes, list):
            self.mimeTypes = [self.mimeTypes]
        
        assert isinstance(self.mimeTypes, list), "mimeTypes were not in a list: %s" % self.mimeTypes
        self.mimeTypes = filter(None, self.mimeTypes)
        
        try:
            self.startIndex = int(self.request.get('i', 0))
        except ValueError:
            self.startIndex = 0

        try:
            self.limit = int(self.request.get('l', 6))
        except ValueError:
            self.limit = 6
        
        self.viewTopics = self.__get_boolean('t', True)
        self.viewPosts = self.__get_boolean('p', False)
        self.viewFiles = self.__get_boolean('f', False)
        self.viewProfiles = self.__get_boolean('r', False)

    def get_title(self):
        if self.searchText:
            s = ', '.join(self.searchTokens.phrases)
            s = 'Results for "%s" in' % s
        else:
            s = 'All'
        
        in_ = []
        if self.view_topics():
            in_.append('topics')
        if self.view_posts():
            in_.append('posts')
        if self.view_files():
            in_.append('files')
        if self.view_profiles():
            in_.append('profiles')
        
        if len(in_) > 1:
            inStr = ', '.join(in_[:-1])
            inStr = '%s and %s' % (inStr, in_[-1])
        else:
            try:
                inStr = in_[0]
            except IndexError:
                inStr = ''
        grp = ''
        if len(self.groupIds) == 1:
            groupInfo = createObject('groupserver.GroupInfo', 
                         self.context, self.groupIds[0])
            grp = ': %s' % groupInfo.get_name()

        auth = ''
        if len(self.authorIds) == 1:
            authorInfo = createObject('groupserver.UserFromId', 
                                      self.context, self.authorIds[0])
            if authorInfo:
                auth = u' by %s' % authorInfo.name

        r = r'%s %s%s%s: %s'
        retval = r % (s, inStr, auth, grp, self.siteInfo.get_name())
        
        return retval

    def search_description(self):
        if self.searchText:
            s = ', '.join(self.searchTokens.phrases)
            s = 'Results for <q>%s</q> in' % s
        else:
            s = 'All'
        
        in_ = []
        if self.view_topics():
            in_.append('topics')
        if self.view_posts():
            in_.append('posts')
        if self.view_files():
            in_.append('files')
        #if self.view_profiles():
        #    in_.append('profiles')
        
        if len(in_) > 1:
            inStr = ', '.join(in_[:-1])
            inStr = '%s and %s' % (inStr, in_[-1])
        else:
            try:
                inStr = in_[0]
            except IndexError:
                inStr = ''

        auth = ''
        if len(self.authorIds) == 1:
            authorInfo = createObject('groupserver.UserFromId', 
                                      self.context, self.authorIds[0])
            if authorInfo:
                link= '<a class="name" href="%s">%s</a>' % \
                    (authorInfo.url, authorInfo.name)
                auth = u' by %s' % link
            
        grp = ''
        if len(self.groupIds) == 1:
            groupInfo = createObject('groupserver.GroupInfo', 
                         self.context, self.groupIds[0])
            link = '<a class="group" href="%s">%s</a>' % \
              (groupInfo.get_url(), groupInfo.get_name())
            grp = u' in the group %s' % link
        else:
            grp = u' in the site %s' % self.siteInfo.get_name()
            
        r = u'%s %s%s%s.' % (s, inStr, auth, grp)
        return r

    def __get_boolean(self, var, default=True):
        """Get a Boolean value from the form
        
        Getting a Boolean value from an HTML form is a stupidly
        difficult task. To preserve sanity, this method performs the
        leg-work.
        
        ARGUMENTS
            var:     A string naming the Boolean variable to get
            default: The default value for var, if not present.
            
        RETURNS
            The value of "var" in the form, or the value of "default" 
            if "var" is not set in the form.
        """
        val = self.request.get(var, default)
        try:
            # since accept should be '1' if set
            val = int(val) and True or False
        except ValueError:
            val = default
        return val
        
    def get_search_url(self, searchText=None, groupId=None, authorId=None,
        viewTopics=None, viewPosts=None, viewFiles=None, viewProfiles=None,
        startIndex=None, limit=None, baseURL=None):
        """Get the URL for a search
        
        Returns the URL for the current search, or a modification of the
        current search based on the values of the arguments.
        """
        if isinstance(searchText, list):
            searchText = ' '.join(searchText).strip()
        
        queries = []
        queries.append(self.get_query(r's=%s', 
                                      self.searchText, searchText))

        if groupId != '':
            if self.memberGroupsOnly:
                queries.append('mg=1')
        
            if self.groupIds:
                for groupId in self.groupIds:
                    queries.append(self.get_query(r'g=%s', 
                                                  groupId, groupId))
            else:
                queries.append('g=')
        else:
            queries.append('g=')
        
        if self.authorIds:
            for authorId in self.authorIds:
                queries.append(self.get_query(r'a=%s', 
                                              authorId, authorId))
        else:
            queries.append('a=')
            
        if self.mimeTypes:
            for mimeType in self.mimeTypes:
                queries.append(self.get_query(r'm=%s', 
                                              mimeType, mimeType))
        else:
            queries.append('m=')
        
        queries.append(self.get_query(r't=%s',
          self.viewTopics, viewTopics, valType=int))
        queries.append(self.get_query(r'p=%s', 
          self.viewPosts, viewPosts, valType=int))
        queries.append(self.get_query(r'f=%s', 
          self.viewFiles, viewFiles, valType=int))
        queries.append(self.get_query(r'r=%s', 
          self.viewProfiles, viewProfiles, valType=int))
          
        queries.append(self.get_query(r'i=%s', self.startIndex, 
          startIndex, valType=int))
        queries.append(self.get_query(r'l=%s', self.limit, limit, 
          valType=int))

        query_string = '&'.join(queries)
        if baseURL == None:
            baseURL = self.request.URL
        retval = '%s?%s' % (baseURL, query_string)
        return retval
        
    def get_query(self, rstr, defaultVal, val=None, valType=str):
        retval = ''
        if val != None:
            retval = rstr % url_quote(valType(val))
        else:
            retval = rstr % url_quote(valType(defaultVal))
        return retval

    def all_site_search_link(self):
        retval = self.get_search_url(groupId='', startIndex=0)
        return retval
        
    def more_link(self):
        retval = ''
        return retval
        
    def next_link(self):
        retval = ''
        return retval
    
    def view_topics(self):
        return self.viewTopics

    def only_topics_shown(self):
        return self.viewTopics and \
          not(self.viewPosts or self.viewFiles or self.viewProfiles)

    def only_topics_link(self):
        retval = self.get_search_url(viewTopics=True, viewPosts=False,
          viewFiles=False, viewProfiles=False, authorId='', startIndex=0)
        return retval

    def view_posts(self):
        return self.viewPosts

    def only_posts_shown(self):
        return self.viewPosts and \
          not(self.viewTopics or self.viewFiles or self.viewProfiles)

    def only_posts_link(self):
        retval = self.get_search_url(viewTopics=False, viewPosts=True, 
          viewFiles=False, viewProfiles=False, startIndex=0)
        return retval

    def view_files(self):
        return self.viewFiles
    
    def only_files_shown(self):
        return self.viewFiles and \
          not(self.viewTopics or self.viewPosts or self.viewProfiles)

    def only_files_link(self):
        retval = self.get_search_url(viewTopics=False, viewPosts=False,
          viewFiles=True, viewProfiles=False, startIndex=0)
        return retval

    def view_profiles(self):
        return self.viewProfiles

    def only_profiles_shown(self):
        return self.viewProfiles and \
          not(self.viewTopics or self.viewPosts or self.viewFiles)
    
    def searching_group(self, groupId):
        return groupId == self.groupId
    
    def group_count(self):
        """ A count of the number of groupIds that we are processing.
        
        """
        return len(self.groupIds)
    
    def only_group_link(self, groupId):
        return self.get_search_url(groupId=groupId, startIndex=0)
    
    def all_groups_link(self):
        return self.get_search_url(groupId='', startIndex=0)

    def author_count(self):
        return len(self.authorIds)
        
    def only_author_link(self, authorId):
        return self.get_search_url(authorId=authorId, startIndex=0)

    def all_authors_link(self):
        return self.get_search_url(authorId='', startIndex=0)
    
    def process_form(self):
        result = {}

        # Unlike the process_form method of GSContent, there is only
        # one possible form, and the content providers do all the 
        # work!
        
        result['error'] = False
        result['message'] = 'Form processed successfully'

class GSSearchATOMView(GSSearchView):
    """View for the ATOM Feed
    
    This is a dirty hack, to get around a nasty disjoint between the
    architecture of search and ATOM. Basically, the feed needs to
    know the date of the most recent post, but "GSSearchView" does
    not know this value, because it does not do the actual searching.
    Instead the content-providers do all the leg-work. This class
    solves the problem by performing a search for the most recent post,
    and returning the date from that.
    
    *shudder*
    """
    def __init__(self, context, request):
        GSSearchView.__init__(self, context, request)
        
        da = self.context.zsqlalchemy 
        assert da, 'No data-adaptor found'
        messageQuery = MessageQuery(self.context, da)
        
        #searchTokens = createObject('groupserver.SearchTextTokens',
        #    self.searchText)

        #siteInfo = createObject('groupserver.SiteInfo', context)
        #self.siteInfo = siteInfo
        #groupsInfo = createObject('groupserver.GroupsInfo', context)
        #if self.groupIds:
        #    self.groupIds = groupsInfo.filter_visible_group_ids(self.groupIds)
        #else:
        #    self.groupIds = groupsInfo.get_visible_group_ids()

        posts = messageQuery.post_search_keyword(self.searchTokens, 
          self.siteInfo.get_id(), self.groupIds, self.authorIds, 
          limit=1, offset=0)

        self.post = None
        if posts:
            self.post = posts[-1]
                
    def most_recent_post_date(self):
        retval = '1970-1-1T00:00:01'
        if self.post:
            retval = self.post['date']
        return retval

class GSSearchGroupView(GSSearchView):
    """View for Searches within Groups
    
    Like a standard search, except that it only works with a group, 
    setting "groupId" to be the ID ofthe containing group.
    """
    def __init__(self, context, request):
        GSSearchView.__init__(self, context, request)
        self.groupInfos = [createObject('groupserver.GroupInfo', context)]
        self.groupIds = [self.groupInfo.get_id()]
        assert self.groupId, "Search outside a group"

    def only_group(self, groupId=None):
        """By definition, only the group is being searched."""
        return True
        
InitializeClass( GSSearchView )
InitializeClass( GSSearchATOMView )
InitializeClass( GSSearchGroupView )


import sys, re, datetime, time
import DateTime, Globals

from zope.component import createObject
from zope.interface import implements
from Products.Five import BrowserView

from interfaces import IGSSearchResults
from queries import MessageQuery


class GSSearchView(BrowserView):

    implements( IGSSearchResults )
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.siteInfo = createObject('groupserver.SiteInfo', 
          self.context)
        
        self.searchText = self.request.get('searchText', '')
        if isinstance(self.searchText, list):
            self.searchText = ' '.join(self.searchText).strip()
            
        self.groupId = self.request.get('groupId', '')
        if self.groupId:
            self.groupInfo = createObject('groupserver.GroupInfo', context, 
               self.groupId)
        else:
            self.groupInfo = None
           
        self.authorId = self.request.get('authorId', '')
        if self.authorId:
            self.authorInfo = createObject('groupserver.AuthorInfo', 
                                           self.context, self.authorId)
        else:
            self.authorInfo = None
           
        try:
            self.startIndex = int(self.request.get('startIndex', 0))
        except ValueError, e:
            self.startIndex = 0

        try:
            self.limit = int(self.request.get('limit', 6))
        except ValueError, e:
            self.limit = 6
        
        self.viewTopics = self.__get_boolean('viewTopics', True)
        self.viewPosts = self.__get_boolean('viewPosts', False)
        self.viewFiles = self.__get_boolean('viewFiles', True)
        self.viewProfiles = self.__get_boolean('viewProfiles', True)

    def get_title(self):
        retval = ''

        if self.searchText:
            s = ', '.join(self.searchText.split())
            s = '%s in' % s
        else:
            s = 'all'
        
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
            inStr = in_[0]
        grp = ''
        if self.groupInfo:
            grp = ': %s' % self.groupInfo.get_name()
        auth = ''
        if self.authorInfo:
            auth = u', by %s' % self.authorInfo.get_realnames()

        r = r'Results for %s %s%s%s: %s'
        retval = r % (s, inStr, auth, grp, self.siteInfo.get_name())
        
        return retval

    def search_description(self):
        retval = ''

        if self.searchText:
            s = ', '.join(self.searchText.split())
            s = '<q>%s</q> in' % s
        else:
            s = 'all'
        
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
            inStr = in_[0]
        grp = ''
        if self.groupInfo:
            link = '<a class="group" href="%s">%s</a>' % \
              (self.groupInfo.get_url(), self.groupInfo.get_name())
            grp = u', in the group %s' % link
            
        auth = ''
        if self.authorInfo:
            link= '<a class="name" href="%s">%s</a>' % \
              (self.authorInfo.get_url(), self.authorInfo.get_realnames())
            auth = u', by %s' % link
            
        r = u'Results for %s %s%s%s.' % (s, inStr, grp, auth)
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
        searchTextQuery = self.get_query(r'searchText=%s', 
                                         self.searchText, searchText)
                                         
        groupIdQuery = self.get_query(r'groupId=%s', 
                                      self.groupId, groupId)
        
        authorIdQuery = self.get_query(r'authorId=%s', 
                                       self.authorId, authorId)
        
        viewTopicsQuery = self.get_query(r'viewTopics=%s',
          self.viewTopics, viewTopics, valType=int)
        viewPostsQuery = self.get_query(r'viewPosts=%s', 
          self.viewPosts, viewPosts, valType=int)
        viewFilesQuery = self.get_query(r'viewFiles=%s', 
          self.viewFiles, viewFiles, valType=int)
        viewProfilesQuery = self.get_query(r'viewProfiles=%s', 
          self.viewProfiles, viewProfiles, valType=int)
          
        si = self.get_query(r'startIndex=%s', self.startIndex, 
          startIndex, valType=int)
        li = self.get_query(r'limit=%s', self.limit, limit, 
          valType=int)

        queries = '&'.join([searchTextQuery, groupIdQuery, authorIdQuery,
                            viewTopicsQuery, viewPostsQuery, viewFilesQuery, 
                            viewProfilesQuery, si, li])
        if baseURL == None:
            baseURL = self.request.URL
        retval = '%s?%s' % (baseURL, queries)
        return retval
        
    def get_query(self, rstr, defaultVal, val=None, valType=str):
        retval = ''
        if val != None:
            retval = rstr % valType(val)
        else:
            retval = rstr % valType(defaultVal)
        return retval

    def all_site_search_link(self):
        retval = self.get_search_url(groupId='')
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
          viewFiles=False, viewProfiles=False, authorId='')
        return retval

    def view_posts(self):
        return self.viewPosts

    def only_posts_shown(self):
        return self.viewPosts and \
          not(self.viewTopics or self.viewFiles or self.viewProfiles)

    def only_posts_link(self):
        retval = self.get_search_url(viewTopics=False, viewPosts=True, 
          viewFiles=False, viewProfiles=False)
        return retval

    def view_files(self):
        return self.viewFiles
    
    def only_files_shown(self):
        return self.viewFiles and \
          not(self.viewTopics or self.viewPosts or self.viewProfiles)

    def only_files_link(self):
        retval = self.get_search_url(viewTopics=False, viewPosts=False,
          viewFiles=True, viewProfiles=False)
        return retval

    def view_profiles(self):
        return self.viewProfiles

    def only_profiles_shown(self):
        return self.viewProfiles and \
          not(self.viewTopics or self.viewPosts or self.viewFiles)
    
    def only_group(self, groupId):
        return groupId == self.groupId
    
    def only_group_link(self, groupId):
        return self.get_search_url(groupId=groupId)
    
    def all_groups_link(self):
        return self.get_search_url(groupId='')

    def only_author(self, authorId=None):
        return bool(self.authorId)
        
    def only_author_link(self, authorId):
        return self.get_search_url(authorId=authorId)

    def all_authors_link(self):
        return self.get_search_url(authorId='')
    
    def process_form(self):
        form = self.context.REQUEST.form
        result = {}

        # Unlike the process_form method of GSContent, there is only
        #   one possible form, and the content providers do all the 
        #   work!
        
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
        
        searchTokens = createObject('groupserver.SearchTextTokens',
            self.searchText)

        siteInfo = createObject('groupserver.SiteInfo', context)
        self.siteInfo = siteInfo
        groupsInfo = createObject('groupserver.GroupsInfo', context)            

        if self.groupId:
            self.groupIds = groupsInfo.filter_visible_group_ids([self.groupId])
        else:
            self.groupIds = groupsInfo.get_visible_group_ids()

        posts = messageQuery.post_search_keyword(searchTokens, 
          siteInfo.get_id(), self.groupIds, [self.authorId], 
          limit=1, offset=0)
        
        self.post = None
        for post in posts:
            self.post = post
                
    def most_recent_post_date(self):
        retval = '1970-1-1T00:00:01'
        if self.post:
            retval = self.post['date']
        return retval
        
Globals.InitializeClass( GSSearchView )
Globals.InitializeClass( GSSearchATOMView )


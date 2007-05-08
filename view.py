import sys, re, datetime, time
import DateTime, Globals

from zope.interface import implements
from Products.Five import BrowserView
from Products.GSContent.interfaces import IGSSiteInfo

from interfaces import IGSSearchResults

class GSSearchView(BrowserView):

    implements( IGSSearchResults )
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.siteInfo = IGSSiteInfo( context )
        
        # I need to fix these up below
        
        self.searchText = self.request.get('searchText', '')
        self.groupId = self.request.get('groupId', '')
        self.startIndex = int(self.request.get('startIndex', 0))
        self.viewTopics = self.__get_boolean('viewTopics', True)
        self.viewPosts = self.__get_boolean('viewPosts', False)
        self.viewFiles = self.__get_boolean('viewFiles', True)
        self.viewProfiles = self.__get_boolean('viewProfiles', True)

    def get_title(self):
        retval = ''
        
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
        if self.groupId:
            grp = ' :%s' % self.groupId
            
        r = r'Search for %s in %s%s: %s'
        retval = r % (self.searchText, inStr, grp, 
                      self.siteInfo.get_name())
        
        return retval

    def __get_boolean(self, var, default=True):
        """Get a Boolean value from the form
        
        Getting a Boolean value from an HTML form is a stupidly
        difficult task. To save sanity, this method performs the
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
        
    def get_search_url(self, searchText=None, groupId=None, 
        viewTopics=None, viewPosts=None, viewFiles=None, viewProfiles=None):
        """Get the URL for a search
        
        Returns the URL for the current search, or a modification of the
        current search based on the values of the arguments.
        """
        if isinstance(searchText, list):
            searchText = ' '.join(searchText)
        searchTextQuery = self.get_query(r'searchText=%s', 
                                         self.searchText, searchText)
        groupIdQuery = self.get_query(r'groupId=%s', 
                                      self.groupId, groupId)
        viewTopicsQuery = self.get_query(r'viewTopics=%s',
          self.viewTopics, viewTopics, valType=int)
        viewPostsQuery = self.get_query(r'viewPosts=%s', 
          self.viewPosts, viewPosts, valType=int)
        viewFilesQuery = self.get_query(r'viewFiles=%s', 
          self.viewFiles, viewFiles, valType=int)
        viewProfilesQuery = self.get_query(r'viewProfiles=%s', 
          self.viewProfiles, viewProfiles, valType=int)

        queries = '&'.join([searchTextQuery, groupIdQuery, viewTopicsQuery,
                            viewPostsQuery, viewFilesQuery, viewProfilesQuery])
        retval = '%s?%s' % (self.request.URL, queries)
        return retval
        
    def get_query(self, rstr, defaultVal, val=None, valType=str):
        retval = ''
        if val != None:
            retval = rstr % valType(val)
        else:
            retval = rstr % valType(defaultVal)
        return retval

    def view_topics(self):
        return self.viewTopics

    def only_topics_shown(self):
        return self.viewTopics and \
          not(self.viewPosts or self.viewFiles or self.viewProfiles)

    def only_topics_link(self):
        retval = self.get_search_url(viewTopics=True, viewPosts=False,
          viewFiles=False, viewProfiles=False)
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

    def view_profiles(self):
        return self.viewProfiles

    def only_profiles_shown(self):
        return self.viewProfiles and \
          not(self.viewTopics or self.viewPosts or self.viewFiles)
            
    def process_form(self):
        form = self.context.REQUEST.form
        result = {}

        # Unlike the process_form method of GSContent, there is only
        #   one possible form, and the content providers do all the 
        #   work!
        
        result['error'] = False
        result['message'] = 'Form processed successfully'

Globals.InitializeClass( GSSearchView )

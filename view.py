import sys, re, datetime, time
import DateTime, Globals

from Products.Five import BrowserView
from Products.GSContent.interfaces import IGSSiteInfo

class GSSearchView(BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.siteInfo = IGSSiteInfo( context )
        
        self.searchText = self.request.get('searchText', '')
        self.groupId = self.request.get('groupId', '')

        self.startIndex = self.request.get('startIndex', 0)

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
    
    def view_topics(self):
        return self.__get_boolean('viewTopics', True)

    def only_topics_shown(self):
        topics = self.__get_boolean('viewTopics', True)
        posts = self.__get_boolean('viewPosts', False)
        files = self.__get_boolean('viewFiles', True)
        profiles = self.__get_boolean('viewProfiles', True)
        return topics and not(posts or files or profiles)

    def only_topics_link(self):
        group = self.groupId and 'groupId=%s&' % self.groupId or ''
        s = r'%s?searchText=%s%s&viewTopics=1&viewFiles=0&viewProfiles=0'
        retval = s % (self.request.URL, self.searchText, group)
        return retval

    def view_posts(self):
        return self.__get_boolean('viewPosts', False)

    def only_posts_shown(self):
        topics = self.__get_boolean('viewTopics', True)
        posts = self.__get_boolean('viewPosts', False)
        files = self.__get_boolean('viewFiles', True)
        profiles = self.__get_boolean('viewProfiles', True)
        return posts and not(topics or files or profiles)

    def only_posts_link(self):
        group = self.groupId and 'groupId=%s&' % self.groupId or ''
        s = r'%s?searchText=%s%s&viewTopics=0&viewFiles=0&viewProfiles=1'
        retval = s % (self.request.URL, self.searchText, group)
        return retval

    def view_files(self):
        return self.__get_boolean('viewFiles', True)
    
    def only_files_shown(self):
        topics = self.__get_boolean('viewTopics', True)
        posts = self.__get_boolean('viewPosts', False)
        files = self.__get_boolean('viewFiles', True)
        profiles = self.__get_boolean('viewProfiles', True)
        return files and not(topics or posts or profiles)

    def view_profiles(self):
        return self.__get_boolean('viewProfiles', True)

    def only_profiles_shown(self):
        topics = self.__get_boolean('viewTopics', True)
        posts = self.__get_boolean('viewPosts', False)
        files = self.__get_boolean('viewFiles', True)
        profiles = self.__get_boolean('viewProfiles', True)
        return profiles and not(topics or posts or files)
            
    def process_form(self):
        form = self.context.REQUEST.form
        result = {}

        # Unlike the process_form method of GSContent, there is only
        #   one possible form, and the content providers do all the 
        #   work!
        
        result['error'] = False
        result['message'] = 'Form processed successfully'

Globals.InitializeClass( GSSearchView )

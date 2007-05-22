from zope.interface import implements
from interfaces import IGSFileSearchResult
from Products.XWFCore.XWFUtils import get_user, get_user_realnames

class GSFileSearchResult(object):
    implements(IGSFileSearchResult)

    def __init__(self, view, context, result):
        self.view = view
        self.context = context
        self.result = result
                
    def get_icon(self):
        mimeType = self.result['content_type']
        fileName = mimeType.replace('/','-')
        retval = '/++resource++fileIcons/%s.png' % fileName
        return retval

    def get_date(self):
        d = self.result['modification_time']
        retval = str(d)
        return retval

    def get_url(self):
        retval = '/r/file/%s' % self.result['id']
        return retval

    def get_title(self):
        retval = self.result['title']
        return retval

    def get_owner_name(self):
        userId = self.result['dc_creator']
        user = self.__get_user(userId)
        if user:
            name = user.getProperty('preferredName')
        else:
            name = userId
        return name
    
    
    def __get_user(self, userId):
        author_cache = getattr(self.view, '__author_object_cache', {})
        user = author_cache.get(userId, None)
        if not user:
            user = get_user(self.context, userId)
            author_cache[userId] = user
            self.view.__author_object_cache = author_cache
            
        return user



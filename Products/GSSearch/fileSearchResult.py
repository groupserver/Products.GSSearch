# coding=utf-8
from urllib import quote
from zope.component import createObject
from zope.interface import implements
from interfaces import IGSFileSearchResult
from Products.XWFCore.XWFUtils import get_user, change_timezone

class GSFileSearchResult(object):
    implements(IGSFileSearchResult)

    def __init__(self, view, context, result):
        self.view = view
        self.context = context
        self.result = result
    
        gId = self.result['group_ids'][0]
        assert gId
        self.groupInfo = createObject('groupserver.GroupInfo', context, gId)
    
    def get_id(self):
        retval = self.result['id']
        return retval
    
    def get_type(self):
        retval = self.result['content_type']
        return retval

    def get_date(self):
        d = self.result['modification_time']
        retval = str(d)
        return retval

    @property
    def rfc3339_date(self):
        dt = self.result['modification_time']
        utcD = change_timezone(dt, 'UTC')
        retval = utcD.strftime('%Y-%m-%dT%H:%M:%SZ')
        assert retval
        return retval

    def get_size(self):
        retval = self.result['size']
        return retval

    def get_url(self):
        if 'image' in self.get_type():
            retval = '/r/img/%s' % self.get_id()
        else:
            t = self.get_title().encode('ascii', 'ignore')
            retval = '/r/file/%s/%s' % (self.get_id(), quote(t))
        retval = '%s%s' % (self.groupInfo.siteInfo.url, retval)
        return retval

    def get_title(self):
        retval = self.result['title'].strip()
        if not retval:
            retval = 'unknown'
        assert retval
        return retval
        
    def get_group_info(self):
        retval = self.groupInfo
        return retval
    
    def get_tags(self):
        tags = u','.join(self.result['tags']).split(u',')
        retval = [t.strip() for t in tags if t]
        return retval
    
    def get_topic_name(self):
        retval = self.result['topic']
        return retval
        
    def get_owner_id(self):
        retval = self.result['dc_creator']
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

    @property
    def thumbnail_url(self):
        retval = ''
        typePart = self.get_type().split('/')[0]
        if typePart == 'image':
            d = {'group': self.get_group_info().relative_url(),
                'fileId': self.get_id(),
                'name':   self.get_title()}
            retval = '%(group)s/files/f/%(fileId)s/resize/405/303/%(name)s' % d
        return retval


#from interfaces import ITopic

from zope.contentprovider.interfaces import IContentProvider, UpdateNotCalled
from zope.interface import implements, Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.component import adapts, provideAdapter
from zope.pagetemplate.pagetemplatefile import PageTemplateFile

class TopicsSearchItemContentProvider(object):
#    implements()
#    adapts(zope.interface.Interface,
#           zope.publisher.interfaces.browser.IDefaultBrowserLayer,
#           zope.interface.Interface)
    
    def __init__(self, context, request, view):
        self.__updated = False
        
    def update(self):
        self.__updated = True

    def render(self):
        if not self.__updated:
            raise UpdateNotCalled

        retval = '''<li>
            <a href="#" class="topic">Frogs</a>

            in <a href="#" class="group">Frog Love</a>
            <span class="postCount"><span class="cardinal">12</span> 
              posts</span>,
            <span class="dates">
              from
              <span class="date">2007-04-12</span>
              to
              <span class="date">2007-04-18</span>

            </span>
  </li>'''
        return retval
        
#zope.component.provideAdapter(IGSTopicsSearchItemContentProvider,
#                              provides=IContentProvider,
#                              name="groupserver.TopicSearchItem")

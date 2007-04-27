import zope.component
import zope.viewlet.interfaces
from zope.contentprovider.interfaces import IContentProvider
from zope.schema import *
from zope.interface import Interface

class IGSSearchFolder(Interface):
    pass

class IGSSearchResults(Interface):
    """The generic search results"""
    
    searchText = TextLine(
        title=u"Search Text",
        description=u"Text that is searched for",
        required=False,
        default=u""
    )

    limit = Int(
        title=u"Limit",
        description=u"Number of items to show in the results",
        required=False,
        min=1,
        default=20,
    )
    
    startIndex = Int(
        title=u"Start Index",
        description=u"The index of the first item show in the results",
        required=False,
        min=0,
        default=0,
    )

class IGSTopicResultsContentProvider(IContentProvider, IGSSearchResults):
    """The GroupServer Topic Results Content Provider"""

    foo = Text(
        title=u"I am a fish", 
        required=False, 
        default=u"bar")

class IGSPostResultsContentProvider(IContentProvider, IGSSearchResults):
      """The GroupServer Post Results Content Provider"""
      
      foo = Text(
          title=u"I am a fish", 
          required=False, 
          default=u"bar")

class IGSFileResultsContentProvider(IContentProvider, IGSSearchResults):
      """The GroupServer File Results Content Provider"""
      
      foo = Text(
          title=u"I am a fish", 
          required=False, 
          default=u"bar")


class IGSProfileResultsContentProvider(IContentProvider, IGSSearchResults):
      """The GroupServer Profile Results Content Provider"""
      
      foo = Text(
          title=u"I am a fish", 
          required=False, 
          default=u"bar")


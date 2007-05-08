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
    
    groupId = TextLine(
        title=u"Group Identifier",
        description=u"Unique Identifier for a group",
        required=False
    )
    
    groupIds = List(
        title=u"Group IDs",
        description=u"The groups to search in; defaults to all visible groups",
        required=False,
        default=[],
        value_type=groupId,
        unique=True,
    )

    limit = Int(
        title=u"Limit",
        description=u"Number of items to show in the results",
        required=False,
        min=1,
        default=6,
    )
    
    startIndex = Int(
        title=u"Start Index",
        description=u"The index of the first item show in the results",
        required=False,
        min=0,
        default=0,
    )
    
    viewTopics = Bool(
        title=u"View Topics",
        description=u"Whether the topic-results should be viewed",
        required=False,
        default=True
    )

    viewPosts = Bool(
        title=u"View Posts",
        description=u"Whether the post-results should be viewed",
        required=False,
        default=False
    )
    
    viewFiles = Bool(
        title=u"View Files",
        description=u"Whether the file-results should be viewed",
        required=False,
        default=True
    )
    
    viewProfiles = Bool(
        title=u"View Profiles",
        description=u"Whether the profile-results should be viewed",
        required=False,
        default=True
    )

class IGSTopicResultsContentProvider(IContentProvider, IGSSearchResults):
    """The GroupServer Topic Results Content Provider"""

    pageTemplateFileName = Text(title=u"Page Template File Name",
      description=u"""The name of the ZPT file that is used to render the
                       results.""",
      required=False,
      default=u"browser/templates/topicResults.pt")
      
    keywordLimit = Int(
        title=u"Keyword Limit",
        description=u"The number of keywords to show in the results",
        required=False,
        min=0,
        default=6,
    )
      
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


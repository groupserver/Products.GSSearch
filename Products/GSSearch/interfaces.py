import zope.component
import zope.viewlet.interfaces
from zope.contentprovider.interfaces import IContentProvider
from zope.schema import *
from zope.interface import Interface

class IGSSearchFolder(Interface):
    pass

class IGSSearchResults(Interface):
    """The generic search results"""
    
    s = TextLine(
        title=u"Search Text",
        description=u"Text that is searched for",
        required=False,
        default=u""
    )
    
    g = TextLine(
        title=u"Group Identifier",
        description=u"Unique Identifier for a group",
        required=False
    )
    
    gs = List(
        title=u"Group IDs",
        description=u"The groups to search in; defaults to all visible groups",
        required=False,
        default=[],
        value_type=g,
        unique=True,
    )

    a = TextLine(
      title=u'Author ID',
      description=u'Unique Identifier of an author',
      required=False
    )

    l = Int(
        title=u"Limit",
        description=u"Number of items to show in the results",
        required=False,
        min=1,
        default=20,
    )
    
    i = Int(
        title=u"Start Index",
        description=u"The index of the first item show in the results",
        required=False,
        min=0,
        default=0,
    )
    
    t = Bool(
        title=u"View Topics",
        description=u"Whether the topic-results should be viewed",
        required=False,
        default=True
    )

    p = Bool(
        title=u"View Posts",
        description=u"Whether the post-results should be viewed",
        required=False,
        default=False
    )
    
    f = Bool(
        title=u"View Files",
        description=u"Whether the file-results should be viewed",
        required=False,
        default=True
    )
    
    r = Bool(
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
    

    pageTemplateFileName = Text(title=u"Page Template File Name",
      description=u"""The name of the ZPT file that is used to render the
                       results.""",
      required=False,
      default=u"browser/templates/postResultsFull.pt")
      
    authorIds = List(
      title=u'Author Ids',
      description=u'Author IDs',
      value_type=TextLine(title=u'Author ID'),
      required=False
    )

class IGSFileResultsContentProvider(IContentProvider, IGSSearchResults):
    """The GroupServer File Results Content Provider"""
    
    pageTemplateFileName = Text(title=u"Page Template File Name",
      description=u"""The name of the ZPT file that is used to render the
                        results.""",
      required=False,
      default=u"browser/templates/fileResults.pt")
      
    searchPostedFiles = Bool(title=u'Search Posted Files',
      description=u'''If True, the files that the users have posted to
        their groups are searched.''',
      required=False,
      default=True)

    searchSiteFiles = Bool(title=u'Search Site Files',
      description=u'''If True, the files in the Web site, outside those
        posted to groups, are searched.''',
      required=False,
      default=True)

class IGSProfileResultsContentProvider(IContentProvider, IGSSearchResults):
      """The GroupServer Profile Results Content Provider"""

class IGSFileSearchResult(Interface):
    pass


class IGSSearchTextTokens(Interface):
    """Splits the search text into tokens, both by phrase and by
    keywords
    """
    
    searchText = TextLine(title=u'Search Text',
      description=u'Text that is searched for',
      required=False,
      default=u'')
      
    phraseDelimiter = TextLine(title=u'Phrase Delimiter',
      description=u'The string that is used to delimit phrases',
      required=False,
      default=u'"')

    nonwords = List(title=u'Non Words',
      description=u'The list of supplied keywords that are also '
        u'stop-words. They are not returned by "keywords".',
      value_type=TextLine(title=u'Word'),
      required=True)
      
    keywords = List(title=u'Keywords',
      description=u'The list of keywords in the search text, ignoring '
        u'phrasing. The text is broken into keywords based on whitespace, '
        u'with "phraseDelimiter" characters stripped. In addition, any'
        u'word that is a stop word is dropped',
      value_type=TextLine(title=u'Keyword'),
      max_length=7,
      required=True)
          
    phrases = List(title=u'Phrases',
      description=u'The list of keywords in the search text, broken '
        u'up by phrases. The text that is not in a phrase is split '
        u'on whitespace.',
      value_type=TextLine(title=u'Phrase'),
      max_length=7,
      required=True)
  

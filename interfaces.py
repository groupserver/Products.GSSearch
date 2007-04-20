from zope.interface import Interface
from zope.schema import Field, Datetime, Int, TextLine, Text, Bool, List
from zope.viewlet.interfaces import IViewletManager
from zope.contentprovider.interfaces import IContentProvider


class IGSSearchFolder(Interface):
  pass

class ITopicSummary(Interface):
  """Summary Information about a topic"""

class IGSTopicsSearchItemContentProvider(IContentProvider):
  """A single-entry in the results for a search of the topics on a site.
  """

import zope.component
import zope.viewlet.interfaces, zope.contentprovider.interfaces 
from zope.schema import *
from zope.interface import Interface

class IGSSearchFolder(Interface):
    pass

# There are six content providers: three for the lists of topics, files
#    and profiles, and three for the respective list-items.

class IGSTopicResultsContentProvider(Interface):
      """The GroupServer Topic Results Content Provider"""
      
      foo = Text(
          title=u"I am a fish", 
          required=False, 
          default=u"bar")

class IGSTopicResultItemContentProvider(Interface):
      """The Content Provider for a single result in the list of topics"""
      
      foo = Text(
          title=u"I am a fish", 
          required=False, 
          default=u"wibble")


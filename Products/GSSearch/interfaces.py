# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright © 2012, 2013, 2014 OnlineGroups.net and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
from __future__ import absolute_import, unicode_literals
from zope.contentprovider.interfaces import IContentProvider
from zope.interface import Interface
from zope.schema import TextLine, List, Bool, Int, ASCIILine, Text


class IGSSearchFolder(Interface):

    pass


class IGSSearchResults(Interface):
    """The generic search results"""

    s = TextLine(
        title="Search Text",
        description="Text that is searched for",
        required=False,
        default=""
    )

    gs = TextLine(
        title="Group Identifier",
        description="Unique Identifier for a group",
        required=False
    )

    g = List(
        title="Group IDs",
        description="The groups to search in; defaults to all visible groups",
        required=False,
        default=[],
        value_type=gs,
        unique=True,
    )

    ais = TextLine(
      title='Author ID',
      description='Unique Identifier of an author',
      required=False
    )

    a = List(
        title="Author IDs",
        description="The author to search with; defaults to any",
        required=False,
        default=[],
        value_type=ais,
        unique=True,
    )

    l = Int(
        title="Limit",
        description="Number of items to show in the results",
        required=False,
        min=1,
        default=20,
    )

    i = Int(
        title="Start Index",
        description="The index of the first item show in the results",
        required=False,
        min=0,
        default=0,
    )

    t = Bool(
        title="View Topics",
        description="Whether the topic-results should be viewed",
        required=False,
        default=True
    )

    p = Bool(
        title="View Posts",
        description="Whether the post-results should be viewed",
        required=False,
        default=False
    )

    f = Bool(
        title="View Files",
        description="Whether the file-results should be viewed",
        required=False,
        default=True
    )

    r = Bool(
        title="View Profiles",
        description="Whether the profile-results should be viewed",
        required=False,
        default=True
    )

    mg = Bool(
        title="Member groups only",
        description="Limit the search to groups in which the user is a "
                        "member only",
        required=False,
        default=False
    )

    ms = ASCIILine(
        title="MIME Type",
        description="MIME Type of the returned file (file search only).",
        required=False
    )
    m = List(
        title='MIME Types',
        description="The file types to search for (file search only).",
        required=False,
        default=[],
        value_type=ms,
        unique=True,
    )

    st = Bool(
        title="Show Thumbnails",
        description="Whether the thumbnails for images should be shown",
        required=False,
        default=None
    )


class IGSTopicResultsContentProvider(IContentProvider, IGSSearchResults):
    """The GroupServer Topic Results Content Provider"""

    pageTemplateFileName = Text(title="Page Template File Name",
      description="""The name of the ZPT file that is used to render the
                       results.""",
      required=False,
      default="browser/templates/topicResults.pt")

    keywordLimit = Int(
        title="Keyword Limit",
        description="The number of keywords to show in the results",
        required=False,
        min=0,
        default=6,
    )


class IGSPostResultsContentProvider(IContentProvider, IGSSearchResults):
    """The GroupServer Post Results Content Provider"""

    pageTemplateFileName = Text(title="Page Template File Name",
      description="""The name of the ZPT file that is used to render the
                       results.""",
      required=False,
      default="browser/templates/postResultsFull.pt")

    authorIds = List(
      title='Author Ids',
      description='Author IDs',
      value_type=TextLine(title='Author ID'),
      required=False
    )


class IGSFileResultsContentProvider(IContentProvider, IGSSearchResults):
    """The GroupServer File Results Content Provider"""

    pageTemplateFileName = Text(title="Page Template File Name",
      description="""The name of the ZPT file that is used to render the
                        results.""",
      required=False,
      default="browser/templates/fileResults.pt")

    searchPostedFiles = Bool(title='Search Posted Files',
      description='If True, the files that the users have posted to'
        'their groups are searched.',
      required=False,
      default=True)

    searchSiteFiles = Bool(title='Search Site Files',
      description='If True, the files in the Web site, outside those'
        'posted to groups, are searched.',
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

    searchText = TextLine(title='Search Text',
      description='Text that is searched for',
      required=False,
      default='')

    phraseDelimiter = TextLine(title='Phrase Delimiter',
      description='The string that is used to delimit phrases',
      required=False,
      default='"')

    nonwords = List(title='Non Words',
      description='The list of supplied keywords that are also '
        'stop-words. They are not returned by "keywords".',
      value_type=TextLine(title='Word'),
      required=True)

    keywords = List(title='Keywords',
      description='The list of keywords in the search text, ignoring '
        'phrasing. The text is broken into keywords based on whitespace, '
        'with "phraseDelimiter" characters stripped. In addition, any'
        'word that is a stop word is dropped',
      value_type=TextLine(title='Keyword'),
      max_length=7,
      required=True)

    phrases = List(title='Phrases',
      description='The list of keywords in the search text, broken '
        'up by phrases. The text that is not in a phrase is split '
        'on whitespace.',
      value_type=TextLine(title='Phrase'),
      max_length=7,
      required=True)

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
from re import compile as re_compile
from zope.cachedescriptors.property import Lazy
from zope.component.interfaces import IFactory
from zope.interface import implements, implementedBy
from gs.core import to_unicode_or_bust
from .interfaces import IGSSearchTextTokens


class GSSearchTextTokensFactory(object):
    implements(IFactory)

    title = 'GroupServer Search Text Tokeniser Factory'
    descripton = 'Create a new tokeniser for search-text'

    def __call__(self, searchText):
        retval = None
        retval = SearchTextTokens()
        retval.set_search_text(searchText)
        retval.set_phrase_delimiter('"')
        assert retval
        return retval

    def getInterfaces(self):
        retval = implementedBy(SearchTextTokens)
        assert retval
        return retval


class SearchTextTokens(object):

    implements(IGSSearchTextTokens)
    __tokenCache = None

    def set_search_text(self, t):
        s = to_unicode_or_bust(t)
        if not isinstance(s, unicode):
            s = ''
        self.searchText = s

    def set_phrase_delimiter(self, phraseDelimiter):
        self.phraseDelimiter = phraseDelimiter

    def __get_tokens(self):
        if self.__tokenCache is not None:
            retval = self.__tokenCache
        else:
            tokens = [t.lower() for t in self.searchText.split()]
            if self.phraseDelimiter in self.searchText:
                retval = [t.strip().strip(self.phraseDelimiter)
                          for t in tokens]
                retval = [t.lower() for t in retval if t]
            else:
                retval = tokens
        return retval

    @Lazy
    def keywords(self):
        tokens = self.__get_tokens()
        # --=mpj17=--
        # FIXME: The following line contains a UI bug: we never
        #   tell the user that the number of keywords is limited to
        #   seven.
        retval = [w for w in tokens][:7]
        return retval

    @Lazy
    def phrases(self):
        if (self.phraseDelimiter not in self.searchText):
            retval = self.keywords
        else:
            retval = []
            phraseSearchString = '(%s.*?%s)' % (self.phraseDelimiter,
              self.phraseDelimiter)
            phraseSearch = re_compile(phraseSearchString)
            tokens = phraseSearch.split(self.searchText)

            for token in tokens:
                token = token.strip()
                if (token and
                    (token[0] == token[-1] == self.phraseDelimiter)):
                    token = token.strip(self.phraseDelimiter).strip()
                    retval.append(token)
                else:
                    ws = [t.lower() for t in token.split()]
                    retval = retval + ws
            # --=mpj17=-- The following line contains a UI bug: we
            #   never tell the user that the number of phrases is
            #   limited to seven.
            retval = retval[:7]
        return retval

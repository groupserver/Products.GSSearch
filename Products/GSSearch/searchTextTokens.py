# coding=utf-8
import re
import interfaces
from zope.cachedescriptors.property import Lazy
from zope.component.interfaces import IFactory
from zope.interface import implements, implementedBy
from Products.XWFMailingListManager.stopwords import en as STOPWORDS


class GSSearchTextTokensFactory(object):
    implements(IFactory)

    title = u'GroupServer Search Text Tokeniser Factory'
    descripton = u'Create a new tokeniser for search-text'

    def __call__(self, searchText):
        retval = None
        retval = SearchTextTokens()
        retval.set_search_text(searchText)
        retval.set_phrase_delimiter(u'"')
        assert retval
        return retval

    def getInterfaces(self):
        retval = implementedBy(SearchTextTokens)
        assert retval
        return retval


class SearchTextTokens(object):

    implements(interfaces.IGSSearchTextTokens)
    __tokenCache = None

    def set_search_text(self, searchText):
        self.searchText = searchText

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
    def nonwords(self):
        '''When is a word not a word? When it is a stopword!'''
        tokens = self.__get_tokens()
        retval = [w.lower() for w in tokens if w.lower() in STOPWORDS]
        return retval

    @Lazy
    def keywords(self):
        tokens = self.__get_tokens()
        # --=mpj17=--
        # FIXME: The following line contains a UI bug: we never
        #   tell the user that the number of keywords is limited to
        #   seven.
        retval = [w for w in tokens if w not in STOPWORDS][:7]
        return retval

    @Lazy
    def phrases(self):
        if (self.phraseDelimiter not in self.searchText):
            retval = self.keywords
        else:
            retval = []
            phraseSearchString = u'(%s.*?%s)' % (self.phraseDelimiter,
              self.phraseDelimiter)
            phraseSearch = re.compile(phraseSearchString)
            tokens = phraseSearch.split(self.searchText)

            for token in tokens:
                token = token.strip()
                if (token and
                    (token[0] == token[-1] == self.phraseDelimiter)):
                    token = token.strip(self.phraseDelimiter).strip()
                    retval.append(token)
                else:
                    ws = [t.lower() for t in token.split()
                          if t.lower() not in STOPWORDS]
                    retval = retval + ws
            # --=mpj17=-- The following line contains a UI bug: we
            #   never tell the user that the number of phrases is
            #   limited to seven.
            retval = retval[:7]
        return retval

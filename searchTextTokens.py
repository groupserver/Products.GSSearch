import re
import interfaces
from zope.interface import implements
from zope.component.interfaces import IFactory

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
    
    __phraseCache = None
    __keywordCache = None
    
    def set_search_text(self, searchText):
        self.searchText = searchText

    def set_phrase_delimiter(self, phraseDelimiter):
        self.phraseDelimiter = phraseDelimiter
    
    @property
    def keywords(self):
        if self.__keywordCache:
            retval = self.__keywordCache
        else:
            tokens = [t.lower() for t in self.searchText.split()]
            if self.phraseDelimiter in self.searchText:
                retval = [t.strip().strip(self.phraseDelimiter) 
                          for t in tokens]
            else:
                retval = tokens
            self.__keywordCache = retval
        return retval
        
    @property
    def phrases(self):
        retval = []
        if self.__phraseCache:
            retval = self.__phraseCache
        else:
            if (self.phraseDelimiter not in self.searchText):
                retval = self.keywords
            else:
                phraseSearchString  = u'(%s.*?%s)' % (self.phraseDelimiter,
                  self.phraseDelimiter)
                phraseSearch = re.compile(phraseSearchString)
                tokens = phraseSearch.split(self.searchText)
                
                for token in tokens:
                    token = token.strip()
                    if token and (token[0] == token[-1] == self.phraseDelimiter):
                        token = token.strip(self.phraseDelimiter).strip()
                        retval.append(token.lower())
                    else:
                        retval = retval + [t.lower() for t in token.split()]
            self.__phraseCache = retval
        return retval



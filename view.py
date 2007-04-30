import sys, re, datetime, time
import Products.Five, DateTime, Globals
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.GSContent.interfaces import IGSSiteInfo

class GSSearchView(Products.Five.BrowserView):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.siteInfo = IGSSiteInfo( context )
        
        self.searchText = self.request.get('searchText', '')

Globals.InitializeClass( GSSearchView )

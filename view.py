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
        self.groupId = self.request.get('groupId', '')

    def process_form(self):
        form = self.context.REQUEST.form
        result = {}

        # Unlike the process_form method of GSContent, there is only
        #   one possible form, and the content providers do all the 
        #   work!
        
        result['error'] = False
        result['message'] = 'Form processed successfully'

Globals.InitializeClass( GSSearchView )

import sys, re, datetime, time
import Products.Five, DateTime, Globals
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class GSSearchView(Products.Five.BrowserView):
    '''View object for editing standard GroupServer content objects'''
    def __init__(self, context, request):
        self.context = context
        self.request = request

Globals.InitializeClass( GSSearchView )

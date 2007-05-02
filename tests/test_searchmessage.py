##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Size adapters for testing

$Id: test_size.py 61072 2005-10-31 17:43:51Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from zope.interface import implements
from zope.app.size.interfaces import ISized

def test_emailmessage():
    """
    Test searching

    Set up:
      >>> from zope.app.testing.placelesssetup import setUp, tearDown
      >>> setUp()
      >>> import Products.Five
      >>> import Products.XWFMailingListManager
      >>> from Products.GSSearch import queries
      >>> from Products.Five import zcml
      >>> from Products.ZSQLAlchemy.ZSQLAlchemy import manage_addZSQLAlchemy

      >>> zcml.load_config('meta.zcml', Products.Five)
      >>> zcml.load_config('permissions.zcml', Products.Five)
      >>> zcml.load_config('configure.zcml', Products.XWFMailingListManager)
      
      >>> alchemy_adaptor = manage_addZSQLAlchemy(app, 'zalchemy')
      >>> alchemy_adaptor.manage_changeProperties( hostname='localhost',
      ...                                             port=5433,
      ...                                             username='onlinegroups',
      ...                                             password='',
      ...                                             dbtype='postgres',
      ...                                             database='onlinegroups.net')
      
      >>> mq = queries.MessageQuery( {}, alchemy_adaptor )
      >>> [t['subject'] for t in mq.topic_search_subect('Avail', 'ogs', [])]
      [u'Availability']
      >>> [t['subject'] for t in mq.topic_search_keyword('fish', 'ogs', [])]
      [u'Availability', u'Interesting site']
      >>> [t['subject'] for t in mq.topic_search_keyword_subject('Avail', 'ogs', [])]
      [u'Availability', u'Permissions on Web Feed']
      >>> mq.count_word_in_topic('fish', '5s7NnxmGiamrckAB4hQTPv')
      22
      >>> mq.topic_word_count('5s7NnxmGiamrckAB4hQTPv')
      22
      
    Clean up:
      >>> tearDown()
      
    """

def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()

if __name__ == '__main__':
    framework()

=====================
``Products.GSSearch``
=====================
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The Search page for GroupServer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Author: `Michael JasonSmith`_
:Contact: Michael JasonSmith <mpj17@onlinegroups.net>
:Date: 2017-04-16
:Organization: `GroupServer.org`_
:Copyright: This document is licensed under a
  `Creative Commons Attribution-Share Alike 4.0 International License`_
  by `OnlineGroups.Net`_.

Introduction
============

GroupServer_ used to have a *Search* page. Actually, it still
does, but it is not linked from anywhere. Instead the
`gs.search.base`_ product and the `gs.group.messages.topic.list`_
product provides most of the functionality that the `Search
views`_ provide.

.. _gs.search.base: https://github.com/groupserver/gs.search.base
.. _gs.group.messages.topic.list:
   https://github.com/groupserver/gs.group.messages.topic.list

Search views
============

There are three views of a search. All are provided in the
context of a folder with the `marker interface`_, and all change
their output depending on the `query API`_.

Search page:
  The *Search* page, ``index.html``, provides an HTML view of a
  search.

Search AJAX:
  The *Search* AJAX, ``search.ajax``, provides an HTML view of a
  search. However, unlike the *Search* page the HTML is a simple
  list, devoid of the rest of the page. This is useful for
  producing HTML that can be added to other pages.

Search ATOM:
  The *Search* ATOM, ``search.atom``, provides an ATOM view of a
  search, used as a **Web feed.**

Marker interface
================

The `Search views`_ appear in a folder that has been decorated
with the ``Products.GSSearch.interfaces.IGSSearchFolder`` marker
interface. During the installation of a GroupServer site a folder
``s`` is created and given this marker.

Query API
=========

The following parameters can be used to change the query. They
can be specified as part of the ``GET`` request for the `Search
views`_.

``searchText``:
  A space-separated list of terms to search for. Boolean keywords
  are not recognised as such, and all keywords are searched for,
  using an **inclusive or.**

``groupId``:
  The ID of the online group to search. If the groupId is not
  present, the entire site is searched.

``limit``:
  The number of results to show, in each category_.

``startIndex``:
  The index of the first item to show, in each category_.

.. _category:

Results categories
------------------

The results are provided in four different categories: topics,
posts, files, and user profiles. All categories except posts are
shown by default. To change which categories are shown, set the
following parameter to either ``1`` to show the category, or
``0`` to disable the category.

================  ================================
Parameter         Description
================  ================================
``viewTopics``    Results for the topics search.
``viewPosts``     Results for the posts=search.
``viewFiles``     Results for the files search.
``viewProfiles``  Results for the profiles search.
================  ================================

Resources
=========

- Code repository:
  https://github.com/groupserver/Products.GSSearch
- Questions and comments to
  http://groupserver.org/groups/development
- Report bugs at https://redmine.iopen.net/projects/groupserver

.. _GroupServer: http://groupserver.org/
.. _GroupServer.org: http://groupserver.org/
.. _OnlineGroups.Net: https://onlinegroups.net
.. _Michael JasonSmith: http://groupserver.org/p/mpj17
.. _Creative Commons Attribution-Share Alike 4.0 International License:
    http://creativecommons.org/licenses/by-sa/4.0/

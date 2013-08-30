# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

from version import get_version

setup(name='Products.GSSearch',
      version=get_version(),
      description="",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        "Environment :: Web Environment",
        "Framework :: Zope2",
        "Intended Audience :: Developers",
        'License :: OSI Approved :: Zope Public License',
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux"
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='search, ATOM, RSS, Web Feed, AJAX, query',
      author='Michael JasonSmith',
      author_email='mpj17@onlinegroups.net',
      url='http://groupserver.org',
      license='ZPL 2.1',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'pytz',
          'sqlalchemy',
          'zope.cachedescriptors',
          'zope.component',
          'zope.contentprovider',
          'zope.interface',
          'zope.pagetemplate',
          'zope.schema',
          'zope.publisher',
          'AccessControl',
          'Zope2',
          'gs.cache',
          'gs.content.base',
          'gs.database',
          'gs.viewlet',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )

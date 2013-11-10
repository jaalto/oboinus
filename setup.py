"""
Oboinus, a X11 background previewer and setter
Copyright 2011 Suniobo <suniobo@fastmail.fm>

This file is part of Oboinus.

Oboinus is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Oboinus is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Oboinus; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
import os
import glob
import sys
import shutil
from distutils.core import setup
from oboinuslib import __version__, __author__, __license__, __email__

# Code for lang files generation is taken from Sonata
# Thanks!
# Create mo files:
if not os.path.exists("mo/"):
    os.mkdir("mo/")

langs = (l[:-3] for l in os.listdir('po') if l.endswith('po')
                                          and l != "messages.po")
for lang in langs:
    print lang
    pofile = os.path.join("po", "%s.po" % lang)
    modir = os.path.join("mo", lang)
    mofile = os.path.join(modir, "oboinus.mo")
    if not os.path.exists(modir):
        os.mkdir(modir)
    os.system("msgfmt %s -o %s" % (pofile, mofile))


setup(name='oboinus',
      version=__version__,
      description='Oboinus, a X11 background previewer and setter',
      author=__author__,
      author_email=__email__,
      url='https://github.com/suniobo/oboinus',
      scripts=['oboinus'],
      packages=['oboinuslib'],
      data_files=[
            ('share/man/man1', ['oboinus.1']),
            ('share/locale/ru/LC_MESSAGES', ['mo/ru/oboinus.mo']),
            ('share/locale/pt_BR/LC_MESSAGES', ['mo/pt_BR/oboinus.mo']),
            ]
     )

========
Oboinus
========

Homepage: https://github.com/suniobo/oboinus

Background previewer and setter for X implemented in Python.
A simple program to choose picture or background color. 
With option --restore, the configured background is set and program exits. 
This can be used in an .xinitrc/.xsession and other window manager startup files.

Example from ~/.xinitrc script: ::

    oboinus --restore &

For this time feh_ is used as back end setter. So it's required by Oboinus. 

.. _feh: http://linuxbrit.co.uk/feh/


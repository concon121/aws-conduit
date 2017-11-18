#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath(os.path.join('..', '..')))

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'
extensions = ['sphinx.ext.doctest',
              'sphinx.ext.mathjax',
              'sphinx.ext.autodoc',
              'sphinx.ext.napoleon']

napoleon_google_docstring = False
napoleon_use_param = False
napoleon_use_ivar = True

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = 'AWS Conduit'
author = 'Connor Bray'
version = '0.0.1'
release = '0.0.1'
language = None
exclude_patterns = []
pygments_style = 'sphinx'
todo_include_todos = True
html_theme = "sphinx_rtd_theme"
html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',
        'searchbox.html',
        'donate.html',
    ]
}
htmlhelp_basename = 'aws_conduitdoc'

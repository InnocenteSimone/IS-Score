# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

project = 'IS-Score'
copyright = '2025, Simone Innocente'
author = 'Simone Innocente'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary'
]

html_theme = "pydata_sphinx_theme"
templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_static_path = ['_static']
# Prevent Sphinx from adding the module name to the function names
add_module_names = False

html_title = 'IS-Score'
html_sidebars = {
  "**": []
}
html_context = {
    "default_mode": "light"
}

html_theme_options = {
    "navbar_end": ["navbar-icon-links","theme-switcher"],
    "icon_links_label": "Quick Links",
    "icon_links": [
        # {
        #     "name": "Slack",
        #     "url": "https://deepchecks.com/slack",
        #     "icon": "fab fa-github",
        # },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/deepchecks/",
            "icon": "fab fa-python",
        }
    ],
}

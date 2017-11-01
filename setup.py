from distutils.core import setup
import sys
import os

if sys.platform.startswith('win'):
    import py2exe
    
setup(name='chomikDownloader',
          version='0.1.2',
          author='adam_gr',
          author_email='adam_gr [at] gazeta.pl',
          description='Downloads files from your account chomikuj.pl',
          package_dir = {'chomikdownloader' : 'src'},
          packages = ['chomikdownloader'],
          options = {"py2exe" : {
                                  "compressed" : True,
                                  "ignores" : ["email.Iterators", "email.Generator"],
                                  "bundle_files" : 1
                                },
                     "sdist"  : {
                                  'formats': 'zip'
                                }
                    },
          scripts = ['chomik_downloader'],
          console = ['chomik_downloader'],
          zipfile = None
         )


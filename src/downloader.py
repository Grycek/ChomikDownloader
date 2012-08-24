'''
Created on 15-08-2012

@author: adam
'''
import view
import model
from chomikbox import Chomik
import getpass
import re
import traceback
import sys
import os
import threading
import urllib
import urllib2
import time

class ReportHook(object):
    def __init__(self, rate_refresh, name, view):
        self.initiatlized = False
        self.rate_refresh = rate_refresh
        self.name         = name
        self.view         = view
    
    def update(self, count, block_size, total):
        if not self.initiatlized:
            self.initiatlized = True
            self.pb = view.ProgressBar(total=total, rate_refresh = self.rate_refresh, count = 0, name = self.name)
            self.view.add_progress_bar(self.pb)
        else:
            self.pb.update(block_size)
            self.view.update_progress_bars()
    
    def remove_pb(self):
        if self.initiatlized:
            self.view.update_progress_bars()
            self.view.delete_progress_bar(self.pb)
            
            

class DownloaderThread(threading.Thread):
    def __init__(self, pool_sema, filepath, url, view_):
        threading.Thread.__init__(self)
        self.pool_sema = pool_sema
        self.filepath  = filepath
        self.view      = view_
        self.url       = url
        self.daemon     = True
    
    def run(self):
        pb = ReportHook(0.5, self.filepath, self.view)
        try:
            opener = urllib.FancyURLopener({}) 
            self.view.print_(self.filepath)
            opener.retrieve(self.url, self.filepath, pb.update )
        finally:
            pb.remove_pb()
            self.pool_sema.release()   
 
                
class Downloader(object):
    def __init__(self, user = None, password = None, view_ = None, model_ = None, debug = False):
        if view_ == None:
            self.view    = view.View()
        else:
            self.view    = view_
        if model_ == None:
            self.model   = model.Model()
        else:
            self.model   = model_
        self.debug            = debug
        self.user             = user
        self.password         = password
        self.notuploaded_file = 'notdownloaded.txt'
        self.uploaded_file    = 'downloaded.txt'
        maxthreads            = 10
        self.pool_sema         = threading.BoundedSemaphore(value=maxthreads)
        self.chomik = Chomik(self.view, self.model)
        if self.user == None:
            self.user     = raw_input('Podaj nazwe uzytkownika:\n')
        if self.password == None:
            self.password = getpass.getpass('Podaj haslo:\r\n')
        self.view.print_('Logowanie')
        if not self.chomik.login(self.user, self.password):
            self.view.print_( 'Bledny login lub haslo' )
            sys.exit(1)
    
    def download_folder(self, chomik_folder_path, disc_folder_path):
        #chidir
        for folder_id, chomik_folder in self.chomik.get_next_folder():
            folder_path = os.path.join(disc_folder_path, chomik_folder[1:255])
            if not os.path.exists( folder_path ):
                os.makedirs( folder_path  )
            for name, url in self.chomik.get_files_list(folder_id):
                filepath = os.path.join(folder_path, name) 
                self.pool_sema.acquire()
                t = DownloaderThread(self.pool_sema, filepath, url, self.view)
                t.daemon = True
                t.start()
        while threading.active_count() > 1:
            time.sleep(1.)
                
                
if __name__ == "__main__":
    d = Downloader("tmp_chomik1", "")
    d.download_folder("", "/tmp")
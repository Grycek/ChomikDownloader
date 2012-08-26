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
    def __init__(self, pool_sema, filepath, chomik_file_path, url, view_, model_):
        threading.Thread.__init__(self)
        self.pool_sema  = pool_sema
        self.filepath   = filepath
        self.chomik_file_path = chomik_file_path
        self.view       = view_
        self.model      = model_
        self.url        = url
        self.daemon     = True
    
    def run(self):
        self.model.add_notuploaded_normal(self.chomik_file_path)
        self.view.print_("Pobieranie:", self.filepath, '\r\n')
        pb = ReportHook(0.5, self.filepath, self.view)
        try:
            opener = urllib.FancyURLopener({}) 
            opener.retrieve(self.url, self.filepath, pb.update )
        except Exception, e:
            self.view.print_("Blad:", e)
            self.view.print_(self.filepath)
            pb.remove_pb()
            self.pool_sema.release()
        else:
            self.model.remove_notuploaded(self.chomik_file_path)
            self.model.add_uploaded(self.chomik_file_path)
            pb.remove_pb()
            self.view.print_("Pobrano:", self.filepath, '\r\n')
            self.pool_sema.release()   
        
 
    
                
class Downloader(object):
    def __init__(self, user = None, password = None, view_ = None, model_ = None, debug = False, threads = 1):
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
        maxthreads            = threads
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
        folder_dom =  self.chomik.chdirs(chomik_folder_path)
        if folder_dom == None:
            return
        chomik_folder_path = [self.user] + [i for i in chomik_folder_path.split("/") if i != ""]
        chomik_folder_path = "/" + "/".join(chomik_folder_path[:-1]) + "/"
        for folder_id, chomik_folder in self.chomik.get_next_folder(folders_dom=folder_dom):
            folder_path      = os.path.join(disc_folder_path, chomik_folder[1:255])
            chomik_path      = chomik_folder_path + chomik_folder
            chomik_path      = chomik_path.replace("//","/")
            if not os.path.exists( folder_path ):
                os.makedirs( folder_path  )
            self.__download_files_in_folder(folder_id, folder_path, chomik_path)
        while threading.active_count() > 1:
            time.sleep(1.)
    
    def __download_files_in_folder(self, folder_id, folder_path, chomik_path):
        for name, url in self.chomik.get_files_list(folder_id):
            filepath         = os.path.join(folder_path, name) 
            chomik_file_path = os.path.join(chomik_path, name)
            if self.model.in_uploaded(chomik_file_path):
                continue
            self.pool_sema.acquire()
            t = DownloaderThread(self.pool_sema, filepath, chomik_file_path, url, self.view, self.model)
            t.start()
            #t.run()
                
                
if __name__ == "__main__":
    d = Downloader("tmp_chomik1", "")
    d.download_folder("asfhnkjasjhdf", "/tmp")
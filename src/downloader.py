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

def download_file(view, pool_sema, filepath, url):
    try:
        print "Start"
        view.print_(filepath)
        urllib.urlretrieve(url, filepath)
        print "End"
    finally:
        pool_sema.release()   
                
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
        maxthreads        = 4
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
                #t = threading.Thread(target = self.__downloader_aux(filepath, url))
                t = threading.Thread(target = download_file(self.view, self.pool_sema, filepath, url) )
                t.daemon = True
                t.start()
                    
    def __downloader_aux(self, filepath, url):
            try:
                print "Start"
                self.chomik.download_file(url, filepath)
                print "End"
            finally:
                self.pool_sema.release()        
                
                
if __name__ == "__main__":
    d = Downloader("tmp_chomik1", "")
    d.download_folder("", "/tmp")
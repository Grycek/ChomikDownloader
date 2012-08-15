#!/usr/bin/env python 
# -*- coding: utf-8 -*- 
# Author: Adam (adam_gr [at] gazeta.pl)
#
# Written: 05/08/2012
#
# Released under: GNU GENERAL PUBLIC LICENSE
#
# Ver: 0.5

import socket
import urllib2
import urllib
import hashlib
import re
import sys
import time
import os
import zlib
#import progress
import view
import traceback
import model
##################
from soap import SOAP
                                 
#############################
glob_timeout = 240
#KONFIGURACJA
#login_ip   = "208.43.223.12"
#login_ip   = "main.box.chomikuj.pl"
login_ip   = "box.chomikuj.pl"
#login_port = 8083
login_port = 80

def print_dict_in_dict(d, root = ""):
    if u"name" in d:
        print d
        print root + "/" + d["name"], d["id"],
        if d["passwd"] == "true":
            print d["password"]
        else:
            print
        root += "/" + d["name"]
    for k,v in d.iteritems():
        if type(v) == type({}):
            print_dict_in_dict(v, root)
        elif type(v) == type([]):
            for inner_dict in v:
                print_dict_in_dict(inner_dict, root)


def change_coding(text):
    try:
        if sys.platform.startswith('win'):
          text = text.decode('cp1250').encode('utf-8')
    except Exception, e:
        print e
    return text

def to_unicode(text):
    try:
        if sys.platform.startswith('win'):
            text = text.decode('cp1250')
        else:
            text = text.decode('utf8')
    except Exception, e:
        print e
    return text



#####################################################################################################
class ChomikException(Exception):
    def __init__(self, filepath, filename, folder_id, chomik_id, token, server, port, stamp, excpt = None):
        Exception.__init__(self)
        self.filepath  = filepath
        self.filename  = filename
        self.folder_id = folder_id
        self.chomik_id = chomik_id
        self.token     = token
        self.server    = server
        self.port      = port
        self.stamp     = stamp
        self.excpt     = excpt
    
    def __str__(self):
        return str(self.excpt)
    
    def get_excpt(self):
    	return self.excpt
    
    def args(self):
        return (self.filepath, self.filename, self.folder_id, self.chomik_id, self.token, self.server, self.port, self.stamp)

#####################################################################################################
#TODO: zmienic cos z kodowaniem
class Chomik(object):
    def __init__(self, view_ = None, model_ = None):
        if view_ == None:
            self.view    = view.View()
        else:
            self.view    = view_
        if model_ == None:
            self.model   = model.Model()
        else:
            self.model   = model_
        self.soap          = SOAP()
        ########
        #root folder
        self.folders_dom   = {}
        self.ses_id        = ''
        self.chomik_id     = '0'
        self.folder_id     = '0'
        self.cur_fold      = []
        self.user          = ''
        self.password      = ''


    def send(self, content):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(glob_timeout)
        sock.connect( (login_ip, login_port) )
        sock.send(content)
        resp = ""
        while True:
            tmp = sock.recv(640) 
            if tmp ==  '':
                break
            resp   += tmp
        sock.close()
        return resp.partition("\r\n\r\n")[2]
                
        
    def login(self, user, password):
        """
        Logowanie sie do chomika
        Zwraca True przy pomyslnym zalogowani, a False wpp
        """
        self.user          = user
        self.password      = password
        if self.relogin() == True:
            self.get_dir_list()
            return True
        else:
            return False

    def relogin(self):
        password = hashlib.md5(self.password).hexdigest()
        xml_dict = [('ROOT',[('name' , self.user), ('passHash', password), ('ver' , '4'), ('client',[('name','chomikbox'),('version','2.0.4.3') ]) ])]
        xml_content = self.soap.soap_dict_to_xml(xml_dict, "Auth").strip()
        xml_len = len(xml_content)
        header  = """POST /services/ChomikBoxService.svc HTTP/1.1\r\n"""
        header += """SOAPAction: http://chomikuj.pl/IChomikBoxService/Auth\r\n"""
        header += """Content-Type: text/xml;charset=utf-8\r\n"""
        header += """Content-Length: %d\r\n""" % xml_len
        header += """Connection: Keep-Alive\r\n"""
        header += """Accept-Language: pl-PL,en,*\r\n"""
        header += """User-Agent: Mozilla/5.0\r\n"""
        header += """Host: box.chomikuj.pl\r\n\r\n"""
        header += xml_content
        resp = self.send(header)
        resp_dict =  self.soap.soap_xml_to_dict(resp)
        status = resp_dict['s:Envelope']['s:Body']['AuthResponse']['AuthResult']['a:status']
        if status != 'Ok':
            self.view.print_( "Blad(relogin):" )
            self.view.print_( status )
            return False
        try:
            chomik_id = resp_dict['s:Envelope']['s:Body']['AuthResponse']['AuthResult']['a:hamsterId']
            ses_id    = resp_dict['s:Envelope']['s:Body']['AuthResponse']['AuthResult']['a:token'] 
            self.ses_id    = ses_id
            self.chomik_id = chomik_id
        except IndexError, e:
            self.view.print_( "Blad(relogin):" )
            self.view.print_( e )
            #self.view.print_( resp )
            return False
        else:
            return True
        

        
    def get_dir_list(self):
        """
        Pobiera liste folderow chomika.
        """
        self.relogin()
        xml_dict = [('ROOT',[('token' , self.ses_id), ('hamsterId', self.chomik_id), ('folderId' , '0'), ('depth' , 0) ])]
        xml_content = self.soap.soap_dict_to_xml(xml_dict, "Folders").strip()
        xml_len = len(xml_content)
        header  = """POST /services/ChomikBoxService.svc HTTP/1.1\r\n"""
        header += """SOAPAction: http://chomikuj.pl/IChomikBoxService/Folders\r\n"""
        header += """Content-Type: text/xml;charset=utf-8\r\n"""
        header += """Content-Length: %d\r\n""" % xml_len
        header += """Connection: Keep-Alive\r\n"""
        header += """Accept-Language: pl-PL,en,*\r\n"""
        header += """User-Agent: Mozilla/5.0\r\n"""
        header += """Host: box.chomikuj.pl\r\n\r\n"""
        header += xml_content
        resp = self.send(header)
        resp_dict =  self.soap.soap_xml_to_dict(resp)
        status = resp_dict['s:Envelope']['s:Body']['FoldersResponse']['FoldersResult']['a:status']
        if status != 'Ok':
            self.view.print_( "Blad(pobieranie listy folderow):" )
            self.view.print_( status )        
            return False
        self.folders_dom = resp_dict['s:Envelope']['s:Body']['FoldersResponse']['FoldersResult']['a:folder']
        return True


    def cur_adr(self, atr = None):
        """
        Zwracanie lub ustawianie obecnego polozenia w katalogach
        """
        if atr == None:
            return self.cur_fold, self.folder_id
        else:
            self.cur_fold, self.folder_id = atr

    
    def get_next_folder(self, folders_dom = None, root = ""):
        if folders_dom == None:
            folders_dom = self.folders_dom
        if u"name" in folders_dom:
            yield (folders_dom["id"], root + "/" + folders_dom["name"])
            root += "/" + folders_dom["name"]
        for k,v in folders_dom.iteritems():
            if type(v) == type({}):
                for i in self.get_next_folder(v, root):
                    yield i
            elif type(v) == type([]):
                for inner_dict in v:
                    for i in self.get_next_folder(inner_dict, root):
                        yield i

                        
    def get_files_list(self, folder_id):
        #TODO: nie wiem jaki ma byc stamp
        stamp = 0
        reqid =  str(self.chomik_id) + "/" + str(folder_id)
        xml_dict = [('ROOT', [('token', self.ses_id), ( 'sequence', [('stamp', stamp), ('part', 0), ('count', 1), ]), ('disposition', 'download'), ('list', [('DownloadReqEntry', [('id', reqid), ('agreementInfo', [('AgreementInfo',[('name', 'own')])])] )]) ] ) ]
        xml_content = self.soap.soap_dict_to_xml(xml_dict, "Download").strip()
        xml_len = len(xml_content)
        header  = """POST /services/ChomikBoxService.svc HTTP/1.1\r\n"""
        header += """SOAPAction: http://chomikuj.pl/IChomikBoxService/Download\r\n"""
        header += """Content-Type: text/xml;charset=utf-8\r\n"""
        header += """Content-Length: %d\r\n""" % xml_len
        header += """Connection: Keep-Alive\r\n"""
        header += """Accept-Language: pl-PL,en,*\r\n"""
        header += """User-Agent: Mozilla/5.0\r\n"""
        header += """Host: box.chomikuj.pl\r\n\r\n"""
        header += xml_content
        resp = self.send(header)
        resp_dict =  self.soap.soap_xml_to_dict(resp)
        status = resp_dict['s:Envelope']['s:Body']['DownloadResponse']['DownloadResult']['a:status']
        if status != 'Ok':
            self.view.print_( "Blad(pobieranie listy plikow z folderu %s):" % str(folder_id) )
            self.view.print_( status )        
            return False
        file_list = resp_dict['s:Envelope']['s:Body']['DownloadResponse']['DownloadResult']['a:list']['DownloadFolder']['files']
        return [i for i in self.__get_files_list_aux(file_list)]

            
    def __get_files_list_aux(self, files_dict):
        if files_dict == None or files_dict == "None":
            pass
        else:
            files_list = files_dict["FileEntry"]
            if type(files_list) == type({}):
                yield (files_list["name"], files_list["url"])
            elif type(files_list) == type([]):
                for inner_dict in files_list:
                    yield (inner_dict["name"], inner_dict["url"])
    
    def download_file(self, url, filepath):
        urllib.urlretrieve(url, filepath)
        

    def download_token(self):
        reqid = 353442452
        stamp = 2
        xml_dict = [('ROOT', [('token', self.ses_id), ( 'sequence', [('stamp', stamp), ('part', 0), ('count', 1), ]), ('disposition', 'download'), ('list', [('DownloadReqEntry', [('id', reqid), ('agreementInfo', [('AgreementInfo',[('name', 'own')])])] )]) ] ) ]
        xml_dict = [('ROOT', [('token', self.ses_id), ( 'sequence', [('stamp', stamp), ('part', 0), ('count', 1), ]), ('disposition', 'player.audio'), ('list', [('DownloadReqEntry', [('id', reqid), ('agreementInfo', [('AgreementInfo',[('name', 'access')])])] )]) ] ) ]
        #reqid = "20188/1616"
        #xml_dict = [('ROOT', [('token', self.ses_id), ( 'sequence', [('stamp', stamp), ('part', 0), ('count', 1), ]), ('disposition', 'download'), ('list', [('DownloadReqEntry', [('id', reqid)] )]) ] ) ]
        xml_content = self.soap.soap_dict_to_xml(xml_dict, "Download").strip()
        xml_len = len(xml_content)
        header  = """POST /services/ChomikBoxService.svc HTTP/1.1\r\n"""
        header += """SOAPAction: http://chomikuj.pl/IChomikBoxService/Download\r\n"""
        header += """Content-Type: text/xml;charset=utf-8\r\n"""
        header += """Content-Length: %d\r\n""" % xml_len
        header += """Connection: Keep-Alive\r\n"""
        header += """Accept-Language: pl-PL,en,*\r\n"""
        header += """User-Agent: Mozilla/5.0\r\n"""
        header += """Host: box.chomikuj.pl\r\n\r\n"""
        header += xml_content
        resp = self.send(header)
        print resp
        resp_dict =  self.soap.soap_xml_to_dict(resp)
        print resp_dict

        
        
        
if __name__ == "__main__":
    c = Chomik()
    c.login()
    for i in c.get_next_folder():
        print i
        print c.get_files_list(i[0])
    #print c.chomik_id
    #print c.folders_dom
    #c.download_token()

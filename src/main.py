#!/usr/bin/env python 
# -*- coding: utf-8 -*-
'''
Created on 25-08-2012

@author: adam
'''
import downloader   
import sys
import getopt

def usage():
    print 'Użycie programu:'
    print 'python', sys.argv[0], '[-h|--help] [-t|--threads]  [-l|--login nazwa_chomika] [-p|--password haslo chomika] "katalog_na_chomikuj" "katalog_lokalny"\n'
    print '-h,--help\t\t pokazuje pomoc programu'
    print '-l,--login\t\t login/nazwa_uzytkownika do chomika'
    print '-p,--password\t\t haslo do chomika. Przyklad:',
    print 'python', sys.argv[0], '-l nazwa_chomika -p haslo "/katalog1/katalog2/katalog3" "/home/nick/Dokumenty/"'
    print '-t, --threads\t\t liczba watkow (ile plikow jest jednoczescnie wysylanych). Przyklad: ',
    print 'python', sys.argv[0], '-t 5 -r "/katalog1/katalog2/katalog3" "/home/nick/Dokumenty"'

    
if True:
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hl:p:t:', ['help','login', 'password','threads'])
    except Exception, e:
        print 'Przekazano niepoprawny parametr'
        print e
        usage()
        sys.exit(2)
    
    if len(args) != 2:
        usage()
        sys.exit()
    
    login    = None
    password = None
    threads  = 1
    debug    = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-l', '--login'):
            login = arg
        elif opt in ('-p', '--password'):
            password = arg
        elif opt in ('-t', '--threads'):
            threads = int(arg)
        elif opt in ('-d', '--debug'):
            debug = True
    d = downloader.Downloader(login, password,  debug = debug, threads = threads)
    d.download_folder(args[0], args[1])


#!/usr/bin/env python
# encoding: utf8
import re
import sys
import os
from optparse import OptionParser
import webbrowser
import flickrapi
import flickr_cli
from ConfigParser import ConfigParser

config = ConfigParser()
config.read('flickr.config')
api_key = config.get('flickr', 'key')
secret = config.get('flickr', 'secret')


def read_items(path) :
    items = []
    if os.path.exists(path) :
        try :
            fd = open(path)
            items = [line.rstrip() for line in fd if re.search(r'^\S.*$', line) != None]
            fd.close()
        except IOError as e:
            logging.warning(e)
    return items

def make_tags(dir, tags) :
    set0 = set(tags or [])
    set1 = set(read_items('%s/tags.txt' % dir))
    return set0.union(set1)

def make_title(dir, pset) :
    items = read_items('%s/title.txt' % dir)
    if len(items) > 0 :
        return items[0]
    return pset
    
def photoset_default_title(d):
    name = os.path.basename(os.path.normpath(d))
    return make_title(d, name)

def is_excluded(path) :
    name = os.path.basename(path)
    return (name == 'tags.txt') or (name == 'title.txt')

def upload_dir_rec0(flickr, directory, depth, tags, photoset, options) :
    tags0 = tags or make_tags(directory, options.tags) or ""
    photoset0 = photoset or photoset_default_title(directory)
    log = options.log

    try :
        files = [('%s/%s' % (directory, x)) for x in os.listdir(directory)]
    except OSError:
        files = []
    regs = [x for x in files if (os.path.isfile(x) and not is_excluded(x))]
    dirs = [x for x in files if os.path.isdir(x)]
    files = None

    print directory, tags0, photoset0

    upload = flickr_cli.DirectoryFilesFlickrUpload(flickr)
    upload(directory=directory, files=regs, pset=photoset0, tags=tags0,
           log=log)
    for subdir in dirs :
        upload_dir_rec0(flickr, subdir, depth +1, tags, photoset, options)
    
def upload_dir_rec(flickr, options) :
    directory = options.directory
    if options.same_recursive :
        tags = make_tags(directory, options.tags) or ""
        photoset = options.photoset or photoset_default_title(directory)
    else :
        tags = None
        photoset = None
    
    upload_dir_rec0(flickr, directory, 0, tags, photoset, options)

def upload_dir(flickr, options) :
    directory = options.directory
    log = options.log
    tags = make_tags(directory, options.tags) or ""
    photoset = options.photoset or photoset_default_title(directory)

    print directory, tags, photoset

    upload = flickr_cli.DirectoryFlickrUpload(flickr)
    upload(directory=directory, pset=photoset, tags=tags,
           log=log)

def divide_files_by_dir(files) :
    dir2files = dict()
    for file in files :
        dir = os.path.dirname(file)
        if dir not in dir2files :
            dir2files[dir] = []
        dir2files[dir].append(file)
    return dir2files.items()

def upload_files(flickr, directory, files, options) :
    tags = make_tags(directory, options.tags) or ""
    photoset = options.photoset or photoset_default_title(directory)
    log = options.log

    print files, tags, photoset

    upload = flickr_cli.DirectoryFilesFlickrUpload(flickr)
    upload(directory=directory, files=files, pset=photoset, tags=tags,
           log=log)


parser = OptionParser(version="1.0")

parser.add_option("-d", "--directory", dest="directory",
                  help="The directory from which you wish to copy the files",
                  metavar="DIRECTORY")

parser.add_option("-p", "--photoset",
                  dest="photoset", default=False,
                  help="the name for the photoset on flickr.")

parser.add_option("-t", "--tags",
                  action="append", dest="tags",
                  help="Tag to apply to pictures in this directory.")

parser.add_option("-q", "--quiet",
                  action="store_false", dest="verbose", default=True,
                  help="don't print status messages to stdout")

parser.add_option("-r", "--recursive",
                  action="store_true", dest="recursive", default=False,
                  help="recursively copy all subdirectories to different photosets")

parser.add_option("-R", "--RECURSIVE",
                  action="store_true", dest="same_recursive", default=False,
                  help="recursively copy all subdirectories to the same photoset. \
      Overrides -r.")

parser.add_option("-l", "--log",
                  dest="log", default=None,
                  help="output uploaded files log.")

(options, args) = parser.parse_args()

flickr = flickrapi.FlickrAPI(api_key, secret)

if not flickr.token_valid(perms=u'write'):
    flickr.get_request_token(oauth_callback=u'oob')
    authorize_url = flickr.auth_url(perms=u'write')
    webbrowser.open_new_tab(authorize_url)
    verifier = unicode(raw_input('Verifier code: '))
    flickr.get_access_token(verifier)

if options.directory != None :
    if options.recursive or options.same_recursive :
        upload_dir_rec(flickr, options)
    else :
        upload_dir(flickr, options)
if args != None :
    for (dir, files) in divide_files_by_dir(args) :
        upload_files(flickr, dir, files, options)

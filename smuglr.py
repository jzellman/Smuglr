import sys
import os
import shelve
import signal
import time

from multiprocessing import cpu_count, Pool
from optparse import OptionParser

import smugmug

def makedir(path):
    """
    Try creating a directory, catch exception (directory already exists)
    """

    try:
        print "Creating directory", path.encode('utf-8')
        os.makedirs(path)
    except OSError:
        pass

def shelf_key(obj):
    """
    Returns a key that is safe for shelfing
    """
    return "{}-{}".format(obj.__class__.__name__, obj.smug_id)

def set_modified(path, datetime):
    """
    Sets the atime and mtime for the particular path
    """
    atime = mtime = time.mktime(datetime.timetuple())
    os.utime(path, (atime, mtime))

def sync_album(args):
    """
    Syncs album with local file system folder
    arg[0] represents the folder
    arg[1] represents the album
    """
    # TODO - is there a better way to support multiple args
    # when usage is with map?
    folder = args[0]
    album = args[1]
    print album.encode('utf-8')

    shelf = shelve.open(os.path.join(folder, ".smuglr"))
    try:

        album_path = os.path.join(folder, album.title)
        album_shelf_key = shelf_key(album)

        # the folder does not exist on disk but the shelf key does
        # exist. Someone probably deleted the album folder, re-download
        force_download = not os.path.exists(album_path) and album_shelf_key in shelf

        if album_shelf_key not in shelf or force_download:
            shelf[album_shelf_key] = album_path
            makedir(album_path)
            set_modified(album_path, album.modified_at)

        for image in album.images():
            image_path = os.path.join(folder, image.album.title, image.file_name)
            image_shelf_key = shelf_key(image)
            if image_shelf_key not in shelf or force_download:
                with open(image_path, "wb") as f:
                    print "Saving image to", image_path.encode('utf-8')
                    f.write(image.data)
                    set_modified(image_path, image.modified_at)
                    shelf[image_shelf_key] = image_path

    finally:
        shelf.close()

if __name__ == "__main__":
    actions = ["albums", "sync-album", "sync"]

    parser = OptionParser(usage="usage: %prog [command ({}) [options] [args]".format(", ".join(actions)))
    parser.add_option("-a", "--account", dest="account",
                      help="Name of the SmugMug account.")
    parser.add_option("-p", "--password", dest="password",
                      help="Site password for the SmugMug account.", default="")
    parser.add_option("-s", "--single", action="store_true",
                      dest="single_threaded",
                      help="Sync albums in a single thread instead of using all cpus (%d). This is slower, but may be beneficial in debugging problems. Only used with 'sync' command." % cpu_count())

    parser.add_option("-d", "--directory", dest="directory",
                      default=None,
                      help="Specify the output directory for albums. Default is '~/Pictures/Smuglr/<account_name>/'")

    actions = ["albums", "sync-album", "sync"]
    try:
        action = sys.argv[1]
    except IndexError:
        action = None
    (options, args) = parser.parse_args(sys.argv[2:])
    if not options.account or action not in actions:
        print parser.print_help()
        sys.exit(0)

    account = options.account
    api_key = '1vKws3yfpiziQCjBvkg6NeD7bI5oTzDl'
    password = options.password
    smugmug.configure(account, api_key)
    if action == "albums":
        for album in smugmug.Album.list(password):
            print album.title.encode('utf-8')
        sys.exit(0)

    if options.directory:
        folder_path = options.directory
    else:
        folder_path = os.path.join("~/Pictures/Smuglr", account)
    folder = os.path.expanduser(folder_path)
    print "Using directory", folder.encode('utf-8')
    makedir(folder)

    if action == "sync-album":
        album_name = args[0]
        print "Syncing album", album_name.encode('utf-8')
        album = smugmug.Album.get(album_name, password)
        if not album:
            print "Album not found"
            sys.exit(0)
        sync_album([folder, album])
    else:
        albums = [ (folder, a) for a in smugmug.Album.list(password)]
        if options.single_threaded:
            for album in albums:
                sync_album(album)
        else:
            pool = Pool(cpu_count())
            pool.map_async(sync_album, albums).get(9999999)

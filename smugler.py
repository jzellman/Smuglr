import os
import shelve
import multiprocessing

import smugmug

def makedir(path):
    """
    Try creating a directory, catch exception (directory already exists)
    """
    
    try:
        print "Creating directory", path
        os.makedirs(path)
    except OSError:
        pass

def shelf_key(obj):
    """
    Returns a key that is safe for shelfing
    """
    return "{}-{}".format(obj.__class__.__name__, obj.smug_id)

def sync_album(args):
    # TODO - is there a better way to support multiple args
    # when usage is with map?
    folder = args[0]
    album = args[1]

    shelf = shelve.open(os.path.join(folder, ".smugler"))
    try:

        album_path = os.path.join(folder, album.title)
        album_shelf_key = shelf_key(album)

        # the folder does not exist on disk but the shelf key does
        # exist. Someone probably deleted the album folder, re-download
        force_download = not os.path.exists(album_path) and album_shelf_key in shelf

        if album_shelf_key not in shelf or force_download:
            shelf[album_shelf_key] = album_path
            makedir(album_path)
    
        for image in album.images():
            image_shelf_key = shelf_key(image)
            if image_shelf_key not in shelf or force_download:
                image_path = os.path.join(folder, image.album.title, image.file_name)
                with open(image_path, "wb") as f:
                    print "Saving image to", image_path
                    f.write(image.data)
                    shelf[image_shelf_key] = image_path
    finally:
        shelf.close()

if __name__ == "__main__":
    folder = os.path.expanduser("~/Pictures/Smugler")
    print "Using folder", folder
    makedir(folder)
    
    smugmug.configure("zellman", "1vKws3yfpiziQCjBvkg6NeD7bI5oTzDl")

    albums = [ (folder, a) for a in smugmug.Album.list('bigwill')]

    pool = multiprocessing.Pool(10)
    pool.map(sync_album, albums)

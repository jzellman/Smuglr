"""
Simple API to retrieve albums and photos/videos from SmugMug

"""
import json
import urllib
import urllib2
from datetime import datetime

def configure(nickname, key):
    """
    Configures SmugMugClient to use nickname and API key
    """
    SmugMugClient.NICKNAME = nickname
    SmugMugClient.KEY = key

class SmugMugClient(object):
    URL = 'https://secure.smugmug.com/services/api/json/1.3.0/'
    NICKNAME = None
    KEY = None

    @classmethod
    def make_request(self, api_endpoint, **kwargs):
        """
        Make a request to SmugMug
        api_endpoint is the method to hit on SmugMug's API
        """
        params = kwargs.get("params", {})
        params.update({"NickName": self.NICKNAME,
                       "APIKey": self.KEY,
                       "method": api_endpoint})
        params = urllib.urlencode(params)
        request = urllib2.Request(self.URL, params)
        decoder = json.JSONDecoder()
        data = decoder.decode(urllib2.urlopen(request).read())
        
        if data['stat'] != 'ok':
            raise Exception("Error with api endpoint {}. Got {}".
                            format(api_endpoint, data))
        return data
    
    @property
    def modified_at(self):
        """
        Returns a datetime based on LastUpdated property
        """
        return datetime.strptime(self.details['LastUpdated'], '%Y-%m-%d %H:%M:%S')


class Image(SmugMugClient):
    """
    Represents an Image or Video(SmugMug does not decipher between the 2)
    on the SmugMug service
    """
    def __init__(self, album, smug_id, key):
        self._details = None
        self.album = album
        self.key = key
        self.smug_id = smug_id
        self._data = self._details = None

    @classmethod
    def list(self, album):
        """
        Returns a list of Image for a particular Album
        """
        _images = []
        result = self.make_request('smugmug.images.get',
                                   params={"AlbumID": album.smug_id,
                                           "AlbumKey": album.key,
                                           'Password': album.album_password})
        
        for i_data in result['Album']['Images']:
            i = Image(album, i_data['id'], i_data['Key'])
            _images.append(i)
        return _images

    @property
    def details(self):
        """
        Lazy dict of Image details
        """
        
        if self._details is None:
            result = self.make_request("smugmug.images.getInfo",
                                       params = {'ImageID': self.smug_id,
                                                 'ImageKey': self.key,
                                                 'Password': self.album.album_password})
            self._details = result['Image']
        return self._details

    @property
    def data(self):
        """
        Lazy loaded image data
        """
        if self._data is None:
            self._data = urllib.urlopen(self.url).read()
        return self._data

    @property
    def url(self):
        """
        Returns the original res image url or the high res video url 
        """

        if 'Video960URL' in self.details:
            return self.details['Video960URL']
        else:
            return self.details['OriginalURL']

    @property
    def file_name(self):
        """
        Returns the filename
        """
        
        return self.details['FileName']

    def __repr__(self):
        return "<Image %s %s>" % (self.smug_id, self.url)


class Album(SmugMugClient):
    """
    Represents a SmugMug album
    """
    def __init__(self, title, key, smug_id, album_password):
        self.title = title
        self.key = key
        self.smug_id = smug_id
        self.album_password = album_password
        self._details = None

    def __repr__(self):
        return "<Album %s %s>" % (self.title, self.key)

    @classmethod
    def list(self, album_password):
        """
        Returns a list of albums stored on SmugMug. Only supports 1 album password
        """
        _albums = []
        for album_data in self.make_request('smugmug.albums.get')['Albums']:
            #category = Category(album_data['Category']['Name'], album_data['Category']['id'])
            album = Album(album_data['Title'], album_data['Key'], album_data['id'], album_password)

            if not album.details["External"]:
                raise Exception("{} is not external linkable".format(album.title))
                
            _albums.append(album)
        return _albums

    @classmethod
    def get(self, album_name, album_password):
        """
        Returns the album with album_name using album_password
        """
        for album in self.list(album_password):
            if album.title == album_name:
                return album

    @property
    def details(self):
        """
        Lazy loaded album details 
        """
        if self._details is None:
            self._details = self.make_request('smugmug.albums.getInfo',
                                              params = { "AlbumID": self.smug_id,
                                                         "AlbumKey": self.key,
                                                         "Password": self.album_password
                                                         })["Album"]
        return self._details

    def images(self):
        """
        Returns list of images for Album
        """
        return Image.list(self)


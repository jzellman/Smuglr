import json
import urllib
import urllib2
from datetime import datetime

def configure(nickname, key):
    SmugMugClient.NICKNAME = nickname
    SmugMugClient.KEY = key

class SmugMugClient(object):
    URL = 'https://secure.smugmug.com/services/api/json/1.3.0/'
    NICKNAME = None
    KEY = None

    @classmethod
    def make_request(self, api_endpoint, **kwargs):
        params = kwargs.get("params", {})
        params.update({"NickName": self.NICKNAME,
                       "APIKey": self.KEY,
                       "method": api_endpoint})
        params = urllib.urlencode(params)
        request = urllib2.Request(self.URL, params)
        decoder = json.JSONDecoder()
        data = decoder.decode(urllib2.urlopen(request).read())
        
        if data['stat'] != 'ok':
            raise Exception("Error with api endpoint %s. Got %s" % (api_endpoint, data))
        return data
    
    @property
    def modified_at(self):
        return datetime.strptime(self.details['LastUpdated'], '%Y-%m-%d %H:%M:%S')


class Image(SmugMugClient):
    def __init__(self, album, smug_id, key):
        self._details = None
        self.album = album
        self.key = key
        self.smug_id = smug_id
        self._data = self._details = None

    @classmethod
    def list(self, album):
        _images = []
        for i_data in self.make_request('smugmug.images.get',
                                        params={"AlbumID": album.smug_id,
                                                "AlbumKey": album.key,
                                                'Password': album.album_password})['Album']['Images']:
            i = Image(album, i_data['id'], i_data['Key'])
            _images.append(i)
        return _images

    @property
    def details(self):
        if self._details is None:
            self._details = self.make_request("smugmug.images.getInfo",
                                              params = {'ImageID': self.smug_id,
                                                        'ImageKey': self.key,
                                                        'Password': self.album.album_password})['Image']
        return self._details

    @property
    def data(self):
        if self._data is None:
            self._data = urllib.urlopen(self.url).read()
        return self._data

    @property
    def url(self):
        # TODO - handle videos
        if 'Video960URL' in self.details:
            return self.details['Video960URL']
        else:
            return self.details['OriginalURL']

    @property
    def file_name(self):
        return self.details['FileName']

    def __repr__(self):
        return "<Image %s %s>" % (self.smug_id, self.url)


class Album(SmugMugClient):
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
        for album in self.list(album_password):
            if album.title == album_name:
                return album

    @property
    def details(self):
        if self._details is None:
            self._details = self.make_request('smugmug.albums.getInfo',
                                              params = { "AlbumID": self.smug_id,
                                                         "AlbumKey": self.key,
                                                         "Password": self.album_password
                                                         })["Album"]
        return self._details

    def images(self):
        return Image.list(self)


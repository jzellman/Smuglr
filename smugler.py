import urllib
import urllib2
import json


class Smugler(object):
    URL = 'https://secure.smugmug.com/services/api/json/1.3.0/' 
    def __init__(self, nickname, key):
        self.nickname = nickname
        self.key = key
        self.decoder = json.JSONDecoder()

    def images(self, album, password=None):
        def image_url(image):
            return self.make_request("smugmug.images.getURLs",
                                     params = {'ImageID': image.smug_id,
                                               'ImageKey': image.key,
                                               'Password': password}
                                     )['Image']['OriginalURL']
            
        
        _images = []
        for i_data in self.make_request('smugmug.images.get',
                                        params={"AlbumID": album.smug_id,
                                                "AlbumKey": album.key,
                                                'Password': password})['Album']['Images']:
            i = Image(album, i_data['Key'], i_data['id'])
            i.url = image_url(i)
            return [i]
            _images.append(i)

        return _images
        

    def albums(self):
        _albums = []
        for album_data in self.make_request('smugmug.albums.get')['Albums']:
            category = Category(album_data['Category']['Name'], album_data['Category']['id'])
            _albums.append(Album(album_data['Title'], album_data['Key'],
                                album_data['id'], category))
        return _albums

    def make_request(self, api_endpoint, **kwargs):
        params = kwargs.get("params", {})
        params.update({"NickName": self.nickname,
                       "APIKey": self.key,
                       "method": api_endpoint})
        params = urllib.urlencode(params)
        request = urllib2.Request(self.URL, params)
        data = self.decoder.decode(urllib2.urlopen(request).read())
        if data['stat'] != 'ok':
            raise Exception("Error with api endpoint %s. Got %s" % (api_endpoint, data))
        return data

class Image(object):
    def __init__(self, album, key, smug_id):
        self.url = None
        self.album = album
        self.key = key
        self.smug_id = smug_id
    def __repr__(self):
        return "<Image %s %s>" % (self.smug_id, self.url)

    def image(self):
        return urllib.urlopen(self.url).read()

class Category(object):
    def __init__(self, name, smug_id):
        self.name = name
        self.smug_id = smug_id

    def __repr__(self):
        return "<Category %s>" % self.name

class Album(object):
    def __init__(self, title, key, smug_id, category):
        self.title = title
        self.key = key
        self.smug_id = smug_id
        self.category = category

    def __repr__(self):
        return "<Album %s %s>" % (self.title, self.key)



if __name__ == "__main__":
    s = Smugler("zellman", "1vKws3yfpiziQCjBvkg6NeD7bI5oTzDl")
    from pprint import pprint
    albums = s.albums()
    album = [a for a in albums if a.key == 'bW3m7g'][0]
    print album
    for i in s.images(album, 'bigwill'):
        print i.url
#        with open('%s_%s.jpg' % (album.key, i.key), 'w') as f:
#            f.write(i.image())
#
    



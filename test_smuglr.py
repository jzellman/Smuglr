import datetime
import urllib

import httpretty

from smuglr import BASE_URL, Client

NICKNAME = 'test-nickname'
APIKEY = 'test-api-key'
SITE_PASSWORD = 'site-password'


def load_fixture(name):
    with open('fixtures/' + name, 'rb') as f:
        return f.read()


def fake_image(id, key):
    return {
        'album': {'title': 'Test'},
        'id': id,
        'key': key,
    }


def register_request(method, response=None, params=None):
    params = params or {}

    base_params = {
        'NickName': NICKNAME,
        'APIKey': APIKEY,
        'method': method,
        'SitePassword': SITE_PASSWORD
    }
    params.update(base_params)

    query_params = urllib.parse.urlencode(params)
    url = BASE_URL + '?' + query_params
    httpretty.register_uri(httpretty.GET, url, body=response)


@httpretty.activate
def test_fetch_albums():
    register_request('smugmug.albums.get',
                     load_fixture('smugmug.albums.get.json'))
    client = Client(APIKEY, NICKNAME, SITE_PASSWORD)
    albums = client.fetch_albums()

    assert len(albums) == 2, albums
    assert {'title': 'Album 1', 'id': 1, 'key': 'album-1'} in albums
    assert {'title': 'Album 2', 'id': 2, 'key': 'album-2'} in albums


@httpretty.activate
def test_fetch_album_image_ids():
    register_request(
        'smugmug.images.get',
        params={
            'AlbumId': 1,
            'AlbumKey': 'album-1'
        },
        response=load_fixture('smugmug.images.get.json')
    )

    client = Client(APIKEY, NICKNAME, SITE_PASSWORD)
    album = {
        'id': 1,
        'key': 'album-1',
        'title': 'Test',
    }
    media_items = client.fetch_album_image_ids(album)
    assert len(media_items) == 2

    assert media_items == [
        {
            'id': 1,
            'key': 'image-1',
            'album': {'id': 1, 'key': 'album-1', 'title': 'Test'},
        },
        {
            'id': 2,
            'key': 'video-2',
            'album': {'id': 1, 'key': 'album-1', 'title': 'Test'},
        }
    ]


@httpretty.activate
def test_fetch_image_photo():
    register_request(
        'smugmug.images.getInfo',
        params={
            'ImageId': 1,
            'ImageKey': 'image-1'
        },
        response=load_fixture('smugmug.images.getInfo-image.json')
    )

    client = Client(APIKEY, NICKNAME, SITE_PASSWORD)
    image_info = fake_image(1, 'image-1')

    data = client.fetch_image(image_info)
    assert data == {
        'album': {'title': 'Test'},
        'type': 'photo',
        'id': 1,
        'key': 'image-1',
        'url': 'https://test-nickname.smugmug.com/Family/album-1/i-asdfasdf/0/42424242/O/image.jpg',
        'filename': 'image.jpeg',
        'modified_at': datetime.datetime(2014, 4, 21, 18, 40, 23),
    }


@httpretty.activate
def test_fetch_image_video():
    register_request(
        'smugmug.images.getInfo',
        params={
            'ImageId': 2,
            'ImageKey': 'video-2'
        },
        response=load_fixture('smugmug.images.getInfo-video.json')
    )
    client = Client(APIKEY, NICKNAME, SITE_PASSWORD)
    image_info = fake_image(2, 'video-2')
    data = client.fetch_image(image_info)
    assert data == {
        'album': {'title': 'Test'},
        'type': 'video',
        'id': 2,
        'key': 'video-2',
        'url': 'https://test-nickname.smugmug.com/album-1/i-4418Qs/0/asdfasdf/1280/VIDEO-1280.mp4',
        'filename': 'VIDEO.MP4',
        'modified_at': datetime.datetime(2016, 2, 10, 7, 21, 45),
    }

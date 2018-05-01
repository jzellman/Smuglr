import argparse
import datetime
import json
import os
import time
import urllib
import urllib.parse
import urllib.request

from collections import deque
from copy import deepcopy
from concurrent.futures import ProcessPoolExecutor


BASE_URL = 'https://secure.smugmug.com/services/api/json/1.3.0/'


class Client:
    def __init__(self, api_key, nickname,
                 site_password=None,
                 album_passwords=None):
        self.api_key = api_key
        self.nickname = nickname
        self.site_password = site_password
        self.album_passwords = album_passwords or {}

    def fetch(self, api_endpoint, params=None, album_password=None):
        base_params = {
            'NickName': self.nickname,
            'APIKey': self.api_key,
            'method': api_endpoint,
        }
        if album_password:
            base_params['Password'] = album_password
        elif self.site_password:
            base_params['SitePassword'] = self.site_password

        params = params or {}
        params.update(base_params)

        encoded_params = urllib.parse.urlencode(params)
        request = urllib.request.Request(BASE_URL + '?' + encoded_params)
        data = json.loads(urllib.request.urlopen(request).read())

        if data['stat'] != 'ok':
            raise Exception('Error with api endpoint {}. Got {}'.
                            format(api_endpoint, data))
        return data

    def _parse_modified(self, timestr):
        return datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')

    def fetch_albums(self):
        data = self.fetch('smugmug.albums.get')
        return [{
            'title': album_data['Title'],
            'key': album_data['Key'],
            'id': album_data['id'],
        } for album_data in data['Albums']]

    def fetch_album_image_ids(self, album):
        album_password = self.album_passwords.get(album['title'])

        print(f'Fetching image ids for album {album}.')
        data = self.fetch(
            'smugmug.images.get',
            params={
                'AlbumID': album['id'],
                'AlbumKey': album['key'],
            },
            album_password=album_password
        )

        return [{
            'id': image_data['id'],
            'key': image_data['Key'],
            'album': album
        } for image_data in data['Album']['Images']]

    def _find_url(self, data, url_keys):
        for url_key in url_keys:
            if url_key in data:
                return data[url_key]

    def fetch_image(self, image):
        album_password = self.album_passwords.get(image['album']['title'])
        data = self.fetch(
            'smugmug.images.getInfo',
            params={
                'ImageID': image['id'],
                'ImageKey': image['key'],
            },
            album_password=album_password
        )

        data = data['Image']
        # find the largest video url if present
        media_url = self._find_url(data, [
            'Video1280URL',
            'Video960URL',
            'Video640URL',
            'Video320URL'
        ])
        media_type = 'video' if media_url else 'photo'
        # if video is not prsesent, find the largest photo url
        if not media_url:
            media_url = self._find_url(data, [
                'OriginalURL',
                'X3LargeURL',
                'X2LargeURL',
                'XLargeURL',
                'LargeURL'
            ])

        if not media_url:
            raise Exception(f'Could not find URL in {data}')

        image_details = deepcopy(image)
        image_details.update(
            filename=data['FileName'],
            url=media_url,
            type=media_type,
            modified_at=self._parse_modified(data['LastUpdated']),
        )
        return image_details


def download_image(client, image):
    image = client.fetch_image(image)
    album_dir = image['album']['directory']
    filepath = os.path.join(album_dir,  image['filename'])
    if os.path.exists(filepath):
        print(f'File already exists {filepath}')
    else:
        data = urllib.request.urlopen(image['url']).read()
        with open(filepath, 'wb') as f:
            f.write(data)
    set_modified(filepath, image['modified_at'])


def download(client, directory, album_names=None):
    # make destination directory
    safe_mkdir(directory)

    all_albums = client.fetch_albums()
    if not album_names:
        albums_to_download = all_albums
    else:
        albums_to_download = []
        for album_name in album_names:
            album_to_download = None
            for album in all_albums:
                if album['title'] == album_name:
                    album_to_download = album
                    break
            if not album_to_download:
                raise Exception(f'Could not find album by name "{album_name}"')
            else:
                albums_to_download.append(album_to_download)

    for album in albums_to_download:
        album['directory'] = os.path.join(directory, album['title'])

    with ProcessPoolExecutor() as executor:
        errors = []
        image_jobs = deque()

        album_jobs = deque(executor.submit(client.fetch_album_image_ids, album)
                           for album in albums_to_download)

        process_jobs(album_jobs, errors, lambda result: [
            image_jobs.append(executor.submit(download_image, client, image))
            for image in result])

        process_jobs(image_jobs, errors)
        print('Errors', errors)


def process_jobs(jobs, errors, action=None):
    while jobs:
        current_job = jobs.popleft()
        if not current_job.done():
            jobs.append(current_job)
        elif current_job.exception():
            errors.append(current_job.exception())
        elif action:
            action(current_job.result())


def safe_mkdir(path):
    '''
    Try creating a directory, catch exception (directory already exists)
    '''
    try:
        os.makedirs(path)
    except OSError:
        pass


def set_modified(path, datetime):
    '''
    Sets the atime and mtime for the particular path
    '''
    atime = mtime = time.mktime(datetime.timetuple())
    os.utime(path, (atime, mtime))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    actions = ['list-albums', 'download']
    parser.add_argument('action',
                        help='The action to perform',
                        choices=actions)
    parser.add_argument('-a', '--account',
                        help='Name of the SmugMug account.')
    parser.add_argument('-p', '--password',
                        help='Site password for the SmugMug account.')
    parser.add_argument('-d', '--directory',
                        help='''
                        Specify the output directory for albums. Default is
                        '~/Pictures/Smuglr/<account_name>/' ''',
                        default=None)
    parser.add_argument('--album', action='append',
                        help='''
                        Album name to download. Can provide multiple times.
                        If no album is provided, all albums are downloaded.
                        ''')
    parser.add_argument('--albumpass', action='append',
                        help='''
                        Specific password for an album. For example if the
                        album name is 'Holiday Pictures' and the password
                        is 'foo bar', then it would be provided as
                        --albumpass 'Holiday Pictures:foo bar'.
                        Single quotes are preffered.
                        This option can be provided multiple times for
                        each album requiring a password.
                        ''',
                        default=[])
    args = parser.parse_args()
    album_passwords = dict([album_to_pass.rsplit(':', 1)
                            for album_to_pass in args.albumpass])

    api_key = '1vKws3yfpiziQCjBvkg6NeD7bI5oTzDl'
    client = Client(api_key, args.account, args.password, album_passwords)

    directory = args.directory or f'~/Pictures/Smuglr/{args.account}'
    directory = os.path.expanduser(directory)

    if args.action == 'list-albums':
        for album in client.fetch_albums():
            print(album['title'])
    elif args.action == 'download':
        download(client, directory, args.album)

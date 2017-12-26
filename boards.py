import requests


class BoardProvider():
    def _url(self, key, data=None):
        pass

    def _image_url(self, post_data):
        pass

    def _thumbnail_url(self, post_data):
        pass

    def get_posts(self):
        return requests.get(self._url('list')).json()

    def get_image(self, post_data):
        return requests.get(self._image_url(post_data)).content

    def get_thumbnail(self, post_data):
        return requests.get(self._thumbnail_url(post_data)).content

    def search(self, tags):
        tag_string = "tags=" + '+'.join(tags)
        response = requests.get(self._url('list', tag_string))
        result = []

        if(response.content):
            result = response.json()
        return result


class gelbooru_provider(BoardProvider):
    def _url(self, key, data=None):
        tail = {'list': "&s=post",
                'comments': "&s=comment"}
        return "http://gelbooru.com/index.php?page=dapi&json=1" + \
               "&q=index" + tail[key] + "&" + str(data)

    def _image_url(self, post_data):
        url = post_data['file_url']
        return url

    def _thumbnail_url(self, post_data):
        url = "http://simg3.gelbooru.com/thumbnails/" + \
              post_data['directory'] + '/thumbnail_' + \
              post_data['hash'] + '.jpg'
        return url


class tbib_provider(BoardProvider):
    def _url(self, key, data=None):
        tail = {'list': "&s=post",
                'comments': "&s=comment"}
        return "http://tbib.org/index.php?page=dapi&json=1" + \
               "&q=index" + tail[key] + "&" + str(data)

    def _image_url(self, post_data):
        url = "http://tbib.org//images/" + \
              post_data['directory'] + '/' + post_data['image']
        return url

    def _thumbnail_url(self, post_data):
        url = "http://tbib.org/thumbnails/" + \
              post_data['directory'] + '/thumbnail_' + post_data['image']
        return url

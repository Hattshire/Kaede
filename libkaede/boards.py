import requests


class BoardProvider():
    """Base for a imageboard provider."""

    def _url(self, key, tags=None, page=0):
        """Construct the base url."""
        pass

    def _image_url(self, post_data):
        """Construct the image url."""
        pass

    def _thumbnail_url(self, post_data):
        """Construct the thumbnail url."""
        pass

    def get_posts(self):
        """Retrieve the latest images."""
        return requests.get(self._url('list')).json()

    def get_image(self, post_data):
        """Retrieve an image.

        Args:
            post_data (dict): Image information.
        """
        return requests.get(self._image_url(post_data)).content

    def get_thumbnail(self, post_data):
        """Retrieve a thumbnail.

        Args:
            post_data (dict): Image information.
        """
        return requests.get(self._thumbnail_url(post_data)).content

    def search(self, tags, page=0):
        """Get a list of image informations.

        Args:
            tags (list): A list of tags.
            page (int): Page to retrieve.
        """
        tag_string = '+'.join(tags)
        response = requests.get(self._url('list', tag_string, page))
        result = []

        if(response.content):
            result = response.json()
        for item in result:
            yield item


class GelbooruProvider(BoardProvider):
    """Board provider for Gelbooru."""

    def _url(self, key, tags=None, page=0):
        tail = {'list': "&s=post",
                'comments': "&s=comment"}
        return "http://gelbooru.com/index.php?page=dapi&json=1&q=index" + \
               tail[key] + "&tags=" + str(tags) + "&pid=" + str(page)

    def _image_url(self, post_data):
        url = post_data['file_url']
        return url

    def _thumbnail_url(self, post_data):
        url = "http://simg3.gelbooru.com/thumbnails/" + \
              post_data['directory'] + '/thumbnail_' + \
              post_data['hash'] + '.jpg'
        return url


class TbibProvider(BoardProvider):
    """Board provider for The big image board."""

    def _url(self, key, tags=None, page=0):
        tail = {'list': "&s=post",
                'comments': "&s=comment"}
        return "http://tbib.org/index.php?page=dapi&json=1&q=index" + \
               tail[key] + "&tags=" + str(tags) + "&pid=" + str(page)

    def _image_url(self, post_data):
        url = "http://tbib.org//images/" + \
              post_data['directory'] + '/' + post_data['image']
        return url

    def _thumbnail_url(self, post_data):
        url = "http://tbib.org/thumbnails/" + \
              post_data['directory'] + '/thumbnail_' + post_data['image']
        return url

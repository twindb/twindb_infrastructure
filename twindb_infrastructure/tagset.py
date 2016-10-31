class Tag(object):
    def __init__(self, tag=None, key=None, value=None):
        """
        Init Tag instance from a dictionary

        :param tag: dictionary with a tag definition like
            {u'Value': 'nat', u'Key': 'Name'}
        :param key: string with a tag key
        :param value: string with a tag value
        """
        try:
            self.key = tag['Key']
            self.value = tag['Value']
        except TypeError:
            if isinstance(tag, basestring):
                split_tag = tag.split('=')
                self.key = split_tag[0]
                self.value = split_tag[1]
            elif key and value:
                self.key = key
                self.value = value
            else:
                raise

    def __eq__(self, other):
        return self.key == other.key and self.value == other.value


class TagSet(object):

    def __init__(self, tags=None):
        """
        Init tagset instance from list of tags

        :param tags: list of dictionaries with tags. For example,
            [{u'Value': 'nat', u'Key': 'Name'}]
        """
        self.tags = set()
        for tag_def in tags:
            tag = Tag(tag_def)
            self.tags.add(tag)

    def find(self, tag):
        """
        FInd in a set a tag equal to the given tag
        :param tag: Tag() instance
        :return: Tag() or None if not found
        """
        for t in self.tags:
            if t == tag:
                return t

        return None

    def issubset(self, other):
        """
        Test whether every element in the set is in other.

        :param other: instance of TagSet()
        :return: True or False
        """
        for tag in self.tags:
            if not other.find(tag):
                return False

        return True

    def __repr__(self):
        comma = ''
        space = ''
        result = ''
        for tag in self.tags:
            result += "{comma}{space}{key}={value}".format(
                key=tag.key,
                value=tag.value,
                comma=comma,
                space=space)
            comma = ','
            space = ' '
        return result

    def __eq__(self, other):
        return self.issubset(other) and other.issubset(self)

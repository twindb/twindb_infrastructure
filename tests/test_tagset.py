import pytest
from twindb_infrastructure.tagset import TagSet, Tag


@pytest.fixture
def sample_tag_definition():
    return {
        'Key': 'Name',
        'Value': 'foo'
    }


def test_tag(sample_tag_definition):
    tag = Tag(sample_tag_definition)
    assert tag.key == sample_tag_definition['Key']
    assert tag.value == sample_tag_definition['Value']


def test_tags_equal(sample_tag_definition):
    tag1 = Tag(sample_tag_definition)
    tag2 = Tag(sample_tag_definition)
    assert tag1 == tag2


def test_tagset_init(sample_tag_definition):
    tags = [sample_tag_definition]
    TagSet(tags)


def test_tagset_find(sample_tag_definition):
    tags = [sample_tag_definition]
    tagset = TagSet(tags)
    tag = Tag(sample_tag_definition)
    assert tagset.find(tag)


def test_tagset_issubset():
    big_set = TagSet([
        {
            'Key': 'tag1',
            'Value': 'value1'
        },
        {
            'Key': 'tag2',
            'Value': 'value2'
        },
        {
            'Key': 'tag3',
            'Value': 'value3'
        }
    ])

    small_set = TagSet([
        {
            'Key': 'tag1',
            'Value': 'value1'
        },
        {
            'Key': 'tag2',
            'Value': 'value2'
        }
    ])

    print(big_set)
    print(small_set)
    assert small_set.issubset(big_set)
    assert not big_set.issubset(small_set)


def test_tag_from_str():
    assert Tag('Name=aaa') == Tag(key='Name', value='aaa')


def test_tagset_from_tuple():
    assert TagSet((u'Name=aaa', u'Role=master')) == TagSet([
        {
            'Key': 'Name',
            'Value': 'aaa'
        },
        {
            'Key': 'Role',
            'Value': 'master'
        }
    ])


def test_tag_raises_error():
    with pytest.raises(TypeError):
        Tag(tag=None)


def test_find_returns_none():
    ts = TagSet(['Name=foo'])
    assert ts.find(Tag('Name=bar')) is None

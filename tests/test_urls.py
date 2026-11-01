import pytest

from app.utils.urls import has_valid_host, make_website_id, normalize_link


def test_normalize_strips_scheme_www_and_trailing_slash():
    assert normalize_link("https://www.Example.com/") == "example.com"
    assert normalize_link("http://example.com") == "example.com"
    assert normalize_link("example.com") == "example.com"
    assert normalize_link("http://example.com/path/") == "example.com/path"
    assert normalize_link("example.com/a?x=1") == "example.com/a?x=1"


def test_same_site_always_gets_same_id():
    variants = [
        "https://www.sequoiacap.com/",
        "http://sequoiacap.com",
        "SequoiaCap.com",
        "  sequoiacap.com/  ",
    ]
    assert len({make_website_id(u) for u in variants}) == 1


def test_different_sites_get_different_ids():
    assert make_website_id("a.com") != make_website_id("b.com")
    assert make_website_id("a.com/x") != make_website_id("a.com/y")


def test_id_fits_the_column():
    website_id = make_website_id("example.com")
    assert len(website_id) == 32
    assert website_id.isalnum()


def test_id_is_stable():
    # Guards against accidental changes: these ids are already stored in the DB.
    assert make_website_id("example.com") == make_website_id("https://www.example.com/")
    assert make_website_id("example.com") == __import__("hashlib").sha256(b"example.com").hexdigest()[:32]


@pytest.mark.parametrize("url", ["example.com", "https://a.co/x", "www.firm.vc", "sub.domain.org:8080/p"])
def test_valid_hosts(url):
    assert has_valid_host(url)


@pytest.mark.parametrize("url", ["localhost", "", "http://", "not a url", "foo bar.com", None, 123])
def test_invalid_hosts(url):
    assert not has_valid_host(url)

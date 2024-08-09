"""Helper utilities for url parsing etc. ."""

def extract_url_user_auth(url) -> tuple[str, str, str]:
    """Extract basic url, user and authentication from url scheme.
    
    Returns
    -------
    tuple
        Tuple consisting of the url with authentication stripped
        and username and password if supplied.
    """
    import urllib.parse
    
    split_results = urllib.parse.urlsplit(url=url)
    components = [*split_results]
    components[1] = components[1].split("@")[-1] # remove user:auth info
    return urllib.parse.urlunsplit(components), split_results.username, split_results.password

def guess_suffix_from_url(url) -> str:
    """Try to extract filename suffix from url."""

    return "." + url.split(".")[-1].split("/")[0]

# Pagination handler
# Author: Mohsen Minai


def validate(page, per_page):
    #make sure page params are valid
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 30
    return page, per_page


def pagination_headers(github_headers):
    #copy GitHub's pagination headers to our response
    headers = {}
    if "link" in github_headers:
        headers["Link"] = github_headers["link"]
    return headers








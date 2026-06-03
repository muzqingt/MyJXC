"""
测试辅助函数 — 减少重复代码，统一测试风格
"""
from typing import Any, Optional


def get_page(client: Any, url: str, expected: int = 200, follow: bool = True) -> Any:
    """GET 请求并断言状态码"""
    resp = client.get(url, follow_redirects=follow)
    assert resp.status_code == expected, \
        f"GET {url} expected {expected}, got {resp.status_code}"
    return resp


def post_page(client: Any, url: str, data: dict,
              expected: int = 200, follow: bool = True) -> Any:
    """POST 请求并断言状态码"""
    resp = client.post(url, data=data, follow_redirects=follow)
    assert resp.status_code == expected, \
        f"POST {url} expected {expected}, got {resp.status_code}"
    return resp


def get_json(client: Any, url: str) -> Any:
    """GET 请求并返回 JSON"""
    resp = client.get(url)
    assert resp.status_code == 200, \
        f"GET {url} expected 200, got {resp.status_code}"
    return resp.get_json()


def assert_redirects_to_login(client: Any, url: str) -> None:
    """断言未登录时重定向到登录页"""
    resp = client.get(url, follow_redirects=False)
    assert resp.status_code == 302, \
        f"GET {url} expected 302 redirect, got {resp.status_code}"
    location = resp.headers.get('Location', '')
    assert '/auth/login' in location, \
        f"Expected redirect to login, got {location}"

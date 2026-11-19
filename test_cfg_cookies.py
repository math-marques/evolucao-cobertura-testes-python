from requests.cookies import RequestsCookieJar, remove_cookie_by_name

def test_remove_cookie_by_name_cfg_completo():
    jar = RequestsCookieJar()
    jar.set("session", "abc", domain="example.com", path="/")
    jar.set("session", "def", domain="example.com", path="/v1")
    jar.set("theme", "dark", domain="example.com", path="/")
    jar.set("session", "xyz", domain="other.com", path="/admin")

    # Cobertura contempla esses aqui:
    # - [173 -> 174] (cookie.name != "session", ex: "theme")
    # - [175 -> 176] (domain != "example.com", ex: "other.com")
    # - [177 -> 178] (path != "/v1", ex: "/")
    # - [177 -> 179 -> 181 -> 182] (match exato: "session", "example.com", "/v1")
    remove_cookie_by_name(jar, "session", domain="example.com", path="/v1")
    assert ("session", "example.com", "/v1") not in [(c.name, c.domain, c.path) for c in jar]
    assert len(jar) == 3

    # Para fazer a cobertura do domain=None, path=None e saída direta do loop vazio [172 --> 181 ---> Fim]
    remove_cookie_by_name(jar, "inexistente")
    assert len(jar) == 3

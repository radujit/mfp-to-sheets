from http.cookiejar import CookieJar
from requests.cookies import create_cookie

raw = os.environ["MFP_COOKIES"]
cj = CookieJar()

for line in raw.splitlines():
    if "=" in line:
        k, v = line.split("=", 1)
        cj.set_cookie(
            create_cookie(
                name=k.strip(),
                value=v.strip(),
                domain=".myfitnesspal.com",
                path="/"
            )
        )

client = myfitnesspal.Client(cookiejar=cj)

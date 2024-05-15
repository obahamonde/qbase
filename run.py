import yaml
from jinja2 import Environment, FileSystemLoader
from requests import get

from quipubase.qschemas import cast_to_type, parse_anyof_oneof


def fetch(url: str):
    return get(url, timeout=30).json()


env = Environment(loader=FileSystemLoader("./quipubase/templates"))

env.filters["fetch"] = fetch  # type: ignore
env.filters["schema"] = cast_to_type  # type: ignore
env.filters["fromarray"] = parse_anyof_oneof  # type: ignore
template = env.get_template("meta.j2")


print(template.render(url="https://6bxwkv84qjspb1-5000.proxy.runpod.net/"))

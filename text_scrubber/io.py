import os
import json
from typing import Any, Generator


def read_resource_file(package_path: str, resource_name: str, strip: bool = True) -> Generator[str, None, None]:
    """
    Read and parse the file

    :param package_path: package path where the resource is located
    :param resource_name: path to the resource, relative from package
    :param strip: whether or not to strip a line
    :return: A generator where a single element corresponds to a single line in the file
    """
    # Read the document and remove comment lines
    resource_path = os.path.join(os.path.dirname(package_path), resource_name)
    with open(resource_path, 'r', encoding='utf-8') as f:
        resource = f.read()
        lines = resource.splitlines()
        if strip:
            lines = (line.strip() for line in lines)
        lines = (line for line in lines if line and not line.startswith('#'))
        return lines


def read_resource_json_file(package_path: str, resource_name: str) -> Any:
    """
    Load a resource file using json

    :param package_path: package path where the resource is located
    :param resource_name: path to the resource, relative from package
    :return: Contents of the jsoned file
    """
    # Read the document and remove comment lines
    resource_path = os.path.join(os.path.dirname(package_path), resource_name)
    with open(resource_path, 'r') as f:
        return json.load(f)

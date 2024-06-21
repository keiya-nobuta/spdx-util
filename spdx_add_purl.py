# SPDX-License-Identifier: MIT

from spdx_tools.spdx.model import (Package, ExternalPackageRef, ExternalPackageRefCategory,
                                   SpdxNoAssertion, SpdxNone)
from spdx_tools.spdx.parser.parse_anything import parse_file
from spdx_tools.spdx.writer.json import json_writer
from packageurl import PackageURL
from packageurl.contrib.url2purl import url2purl
from urllib.parse import urlparse
import click
from dataclasses import asdict
import sys
import re


file = None

def purl_is_in(package):
    for ext_ref in package.external_references:
        if ext_ref.category is ExternalPackageRefCategory.PACKAGE_MANAGER and \
           ext_ref.reference_type == 'purl':
               return True

    return False

def add_purl_to_spdx(spdx_json):
    document = parse_file(spdx_json)

    for package in document.packages:
        if purl_is_in(package):
            continue

        purl = None
        download_location = package.download_location

        if type(download_location) not in (SpdxNoAssertion, SpdxNone):
            if re.match('https://.*\.*crates.io.*', download_location):
                # cargo
                purl = PackageURL(type = 'cargo',
                                  name = package.name,
                                  version = package.version)

            if not purl:
                purl = url2purl(download_location)
                if not purl.version:
                    purl = PackageURL(type = 'generic',
                                      name = package.name,
                                      version = package.version,
                                      qualifiers={'download_url': download_location})
        else:
            purl = PackageURL(type='generic', name=package.name, version=package.version)

        if purl:
            package_manager = ExternalPackageRef(
                        category = ExternalPackageRefCategory.PACKAGE_MANAGER,
                        reference_type = 'purl',
                        locator = str(purl))
            package.external_references.append(package_manager)

    json_writer.write_document_to_stream(document, sys.stdout, validate = False)

@click.command()
@click.argument('spdx_json', nargs=1)
def add_purl_to_spdx_cli(spdx_json):
    add_purl_to_spdx(spdx_json)

if __name__ == "__main__":
    add_purl_to_spdx_cli()

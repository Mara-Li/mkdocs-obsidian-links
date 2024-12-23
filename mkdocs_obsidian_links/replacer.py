import posixpath
import re
from typing import Match, Union
from urllib.parse import quote

from .file_mapper import FileMapper
from .scanners.base_link_scanner import BaseLinkScanner
from .types import BrokenLink, LinksOptions


class LinksReplacer:
    def __init__(
        self,
        root: str,
        file_map: FileMapper,
        use_directory_urls: bool,
        options: LinksOptions,
        logger,
    ):
        self.root = root
        self.file_map = file_map
        self.use_directory_urls = use_directory_urls
        self.options = options
        self.scanners = []
        self.logger = logger

    def add_scanner(self, scanner: BaseLinkScanner) -> None:
        self.scanners.append(scanner)

    def replace(self, path: str, markdown: str) -> str:
        self.path = path

        # Multi-Pattern search pattern, to capture  all link types at once
        return re.sub(self.regex, self._do_replace, markdown)

    # Compiles all scanner patterns as a multi-pattern search, with
    # built in code fence skipping (individual link scanners don't
    # have to worry about them.

    def file_exists(self, file_path: str, source: str) -> Union[bool, str]:
        if (
            (
                file_path.startswith("http://")
                or file_path.startswith("https://")
                or file_path.startswith("mailto:")
                or file_path.startswith("www.")
            )
            or posixpath.exists(file_path)
            or posixpath.exists(file_path + ".md")
        ):
            return True

        # try with index file
        return False

    def compile(self):
        patterns = "|".join([scanner.pattern() for scanner in self.scanners])
        self.regex = re.compile(
            rf"""
            (?: # Attempt to match a code block
                [`]{{3}}
                (?:[\w\W]*?)
                [`]{{3}}$
            | # Match an inline code block
                `[\w\W]*?`
            )
            | # Attempt to match any one of the subpatterns
            (?:
                {patterns}
            )
            """,
            re.X | re.MULTILINE,
        )

    def _do_replace(self, match: Match) -> str:
        abs_from = posixpath.dirname(posixpath.join(self.root, self.path))
        try:
            for scanner in self.scanners:
                if scanner.match(match):
                    link = scanner.extract(match)

                    # Do some massaging of the extracted results
                    if not link:
                        raise BrokenLink(
                            f"Could not extract link from '{match.group(0)}'"
                        )
                    broken_link = False
                    # Handle case of local page anchor
                    if not link.target:
                        if link.anchor:
                            link.target = posixpath.join(self.root, self.path)
                            file_exists = self.file_exists(link.target, abs_from)
                            if not file_exists:
                                broken_link = True
                        else:
                            raise BrokenLink(f"No target for link '{match.group(0)}'")
                    else:
                        # Otherwise, search for the target through the file map
                        search_result = self.file_map.search(self.path, link.target)

                        if not self.use_directory_urls:
                            search_result = (
                                search_result + ".md"
                                if "." not in search_result
                                else search_result
                            )
                        if not search_result:
                            raise BrokenLink(f"'{link.target}' not found.")
                        link.target = search_result
                        broken_link = False
                        file_exists = self.file_exists(search_result, abs_from)
                        if not file_exists:
                            broken_link = True
                        else:
                            link.target = search_result

                    link.target = quote(
                        posixpath.relpath(link.target, abs_from).replace("\\", "/")
                    )
                    return link.render(not_found=broken_link)
        except BrokenLink as ex:
            # Log these out as Debug messages, as the regular mkdocs
            # strict mode will log out broken links.
            self.logger.debug(f"[EzLinks] {ex}")

        # Fall through, return the original link unaltered, and let mkdocs handle it
        return match.group(0)

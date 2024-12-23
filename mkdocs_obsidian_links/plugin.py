import logging
from typing import List

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File

from .file_mapper import FileMapper
from .replacer import LinksReplacer
from .scanners.md_link_scanner import MdLinkScanner
from .scanners.reference_link_scanner import ReferenceLinkScanner
from .scanners.wiki_link_scanner import WikiLinkScanner
from .types import LinksOptions

LOGGER = logging.getLogger(f"mkdocs.plugins.{__name__}")


class LinksPlugin(BasePlugin):
    config_scheme = (
        ("wikilinks", config_options.Type(bool, default=True)),
        ("warn_ambiguities", config_options.Type(bool, default=False)),
        ("reference_links", config_options.Type(bool, default=False)),
    )

    def init(self, config):
        self.replacer = LinksReplacer(
            root=config["docs_dir"],
            file_map=self.file_mapper,
            use_directory_urls=config["use_directory_urls"],
            options=LinksOptions(**self.config),
            logger=LOGGER,
        )

        self.replacer.add_scanner(MdLinkScanner())
        if self.config["wikilinks"]:
            self.replacer.add_scanner(WikiLinkScanner())

        if self.config["reference_links"]:
            self.replacer.add_scanner(ReferenceLinkScanner())

        # Compile the regex once
        self.replacer.compile()

    # Build a fast lookup of all files (by file name)
    def on_files(self, files: List[File], config):
        self.file_mapper = FileMapper(
            options=LinksOptions(**self.config),
            root=config["docs_dir"],
            files=files,
            logger=LOGGER,
        )

        # After the file map has been built, initialize what we can that will
        # remain static
        self.init(config)

    def on_page_markdown(self, markdown, page, config, **kwargs):
        return self.replacer.replace(page.file.src_uri, markdown)

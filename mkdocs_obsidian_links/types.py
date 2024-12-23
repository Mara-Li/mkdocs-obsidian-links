from dataclasses import dataclass


class BrokenLink(Exception):  # noqa: N818
    # Ignore these
    pass


@dataclass
class Link:
    """Dataclass to hold the contents required to form a complete Link."""

    image: bool
    text: str
    target: str
    anchor: str
    title: str

    # Render as a complete MD compatible link
    def render(self, not_found=False):
        img = "!" if self.image else ""
        anchor = f"#{self.anchor}" if self.anchor else ""
        title = f' "{self.title}"' if self.title else ""
        broken = "{: .ezlinks_not_found}" if not_found else ""
        if not_found:
            img = ""
        return f"{img}[{self.text}]({self.target}{anchor}{title}){broken}"


@dataclass
class LinksOptions:
    """Dataclass to hold typed options from the configuration."""

    wikilinks: bool
    warn_ambiguities: bool
    reference_links: bool

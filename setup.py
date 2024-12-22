import tomllib

from setuptools import setup, find_packages
import tomllib as toml

description = "A mkdocs plugin that makes linking to other documents easy."
long_description = description

with open(".version", "r") as f:
    version = f.read().strip()


# Charger le Pipfile
with open("Pipfile", "rb") as f:
    pipfile = tomllib.load(f)

# Extraire les dépendances
required = pipfile.get("packages", {})

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="mkdocs-obsidian-links",
    version=version,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="mkdocs, wikilinks, obsidian, roam",
    url="https://github.com/Mara-Li/mkdocs-obsidian-links",
    author="Mara-Li",
    author_email="Mara-Li@outlook.fr",
    license="MIT",
    python_requires=">=3.6",
    install_requires=required,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
    ],
    packages=find_packages(exclude=["test.*"]),
    entry_points={
        "mkdocs.plugins": ["ezlinks = mkdocs_obsidian_links.plugin:LinksPlugin"]
    },
)

"""Contains classes that map :class:`.Item` unique identifiers.

"""
__author__ = 'Paul Landes'

from abc import ABC, abstractmethod
import logging
import re
import unicodedata
from zensols.zotsite import Item, Library

logger = logging.getLogger(__name__)


def slugify(text):
    """Convert text to SEO-friendly URL slug.
    
    Args:
        text: The text to slugify
        
    Returns:
        A URL-safe slug string
    """
    if not text:
        return ''
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Convert to lowercase and replace spaces with hyphens
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text)
    
    # Remove leading/trailing hyphens
    return text.strip('-')[:50]  # Limit length for SEO


class ItemMapper(ABC):
    """Maps :class:`.Item` unique identifiers.

    """
    EXT_RE = re.compile(r'.+\.(.+)?$')

    def _item_to_ext(self, item: Item):
        m = self.EXT_RE.match(item.path.name)
        return f'.{m.group(1)}' if m is not None else ''

    @abstractmethod
    def get_resource_name(self, item: Item) -> str:
        """Return a resource used on the browser side for ``item``."""
        pass

    @abstractmethod
    def get_file_name(self, item: Item) -> str:
        """Return a file path used on the browser side for ``item``."""
        pass


class RegexItemMapper(ItemMapper):
    """Map by using regular expression replacements.

    """
    def __init__(self, lib: Library, fmatch_re=None, repl_re=None):
        self.lib = lib
        if fmatch_re is not None:
            self.fmatch_re = re.compile(fmatch_re)
        else:
            self.fmatch_re = None
        if repl_re is not None:
            self.repl_re = re.compile(repl_re)
        else:
            self.repl_re = None

    def _map(self, item: Item) -> str:
        """Return the regular expression matched/modified string of ``fname``.'

        """
        fname = self.lib.attachment_resource(item)
        if fname is not None:
            if self.fmatch_re and self.repl_re and self.fmatch_re.match(fname):
                fname = self.repl_re.sub('_', fname)
        return fname

    def get_resource_name(self, item: Item) -> str:
        return self._map(item)

    def get_file_name(self, item: Item) -> str:
        return self._map(item)


class IdItemMapper(ItemMapper):
    """Map by using item IDs.

    """
    def __init__(self, lib: Library, fmatch_re=None, repl_re=None):
        self.lib = lib
        if fmatch_re is not None:
            self.fmatch_re = re.compile(fmatch_re)
        else:
            self.fmatch_re = None
        if repl_re is not None:
            self.repl_re = re.compile(repl_re)
        else:
            self.repl_re = None

    def _map(self, item: Item) -> str:
        """Return the regular expression matched/modified string of ``fname``.'

        """
        if item.type == 'attachment' and item.path is not None:
            ext = self._item_to_ext(item)
            return f'{self.lib.storage_dirname}/{item.id}{ext}'

    def get_resource_name(self, item: Item) -> str:
        return self._map(item)

    def get_file_name(self, item: Item) -> str:
        return self._map(item)


class SeoItemMapper(ItemMapper):
    """Map by using SEO-friendly URLs based on item titles and content.

    """
    def __init__(self, lib: Library):
        self.lib = lib
        self._used_slugs = set()  # Track used slugs to avoid duplicates

    def _create_seo_name(self, item: Item) -> str:
        """Create SEO-friendly filename from item metadata."""
        if item.type == 'attachment' and item.path is not None:
            ext = self._item_to_ext(item)
            
            # Try to get a meaningful name from the item
            base_name = ''
            
            # First try the title from metadata
            if hasattr(item, 'meta') and item.meta and 'title' in item.meta:
                base_name = item.meta['title']
            elif hasattr(item, 'title') and item.title:
                base_name = item.title
            elif hasattr(item, 'name') and item.name:
                base_name = item.name
            else:
                # Fall back to filename without extension
                base_name = item.path.stem if item.path else f'item-{item.id}'
            
            # Create slug and ensure uniqueness
            slug = slugify(base_name)
            if not slug:
                slug = f'item-{item.id}'
            
            original_slug = slug
            counter = 1
            while slug in self._used_slugs:
                slug = f'{original_slug}-{counter}'
                counter += 1
            
            self._used_slugs.add(slug)
            return f'{self.lib.storage_dirname}/{slug}{ext}'
        
        return None

    def get_resource_name(self, item: Item) -> str:
        return self._create_seo_name(item)

    def get_file_name(self, item: Item) -> str:
        return self._create_seo_name(item)

"""Baldur's Gate 3 Wiki character scraper adapter.

This module implements content retrieval for Baldur's Gate 3 characters from
the bg3.wiki website, extracting multiple sections (Overview, Description,
Gameplay, History) as clean Markdown with proper formatting.
"""

import copy
import re
from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as md

from learn_ai_agents.application.outbound_ports.content_indexer.source_ingestion.source_ingestion import (
    SourceIngestionPort,
)
from learn_ai_agents.domain.models.content_indexer.source_ingestion import (
    ContentRequest,
    Document,
)
from learn_ai_agents.domain.exceptions import ComponentOperationException, InvalidRequestException, ResourceNotFoundException, SourceContentFormatException
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TopSection:
    """Represents a top-level section from the table of contents."""

    id: str  # HTML anchor id, e.g. "Overview"
    number: str  # "1", "2", "3", ...
    title: str  # "Overview", "Description", ...


class BaldursGate3CharactersAdapter(SourceIngestionPort):
    """Adapter for retrieving BG3 character information from bg3.wiki.

    This adapter fetches character pages from the Baldur's Gate 3 wiki and
    extracts multiple sections (Overview through History) as clean Markdown format.
    It handles proper heading normalization, link stripping, and footnote removal.

    Attributes:
        timeout: Timeout for HTTP requests in seconds.
        headers: Default headers for HTTP requests.
    """

    def __init__(self, timeout: int = 15, headers: dict[str, str] | None = None):
        """Initialize the BG3 characters scraper adapter.

        Args:
            timeout: Timeout for HTTP requests in seconds (default: 15).
            headers: Default headers for HTTP requests.
        """
        self.timeout = timeout
        self.headers = headers or {"User-Agent": "bg3-wiki-scraper/0.1 (personal use)"}
        logger.info("BaldursGate3CharactersAdapter initialized")

    def retrieve_content(self, request: ContentRequest) -> Document:
        """Retrieve character sections from BG3 wiki as clean Markdown.

        Extracts sections from Overview through History (excluding Involvement),
        with proper heading normalization, link text extraction, and footnote removal.

        Args:
            request: ContentRequest with source="web" and params containing:
                - url: The character's wiki page URL

        Returns:
            Document with all sections concatenated as Markdown content and metadata
            containing section details.

        Raises:
            DomainException: If the request is invalid or retrieval fails.
        """
        logger.info(f"Retrieving BG3 character content for request {request.document_id}")

        # Validate request
        if request.source != "web":
            raise InvalidRequestException(params={"source": request.source}, message=f"Invalid source: {request.source}. Expected 'web'")

        if not request.params or "url" not in request.params:
            raise InvalidRequestException(params=request.params, message="Missing 'url' parameter in request")

        url = request.params["url"]
        logger.debug(f"Fetching character content from URL: {url}")

        try:
            # Fetch and parse the page
            html = self._fetch_html(url)
            soup = BeautifulSoup(html, "html.parser")

            # Parse table of contents for top-level sections
            toc_sections = self._parse_top_level_toc(soup)

            # Select sections from Overview until History (exclude Involvement)
            selected = []
            for sec in toc_sections:
                if sec.title.strip().lower() == "involvement":
                    break
                selected.append(sec)
            
            if not selected:
                # Page exists but doesn't have the structure we expect
                raise SourceContentFormatException(
                    content_type="web",
                    message=f"No usable sections found for BG3 character at {url}",
                )

            # Extract each section as Markdown
            result_sections = []
            markdown_parts = []

            for sec in selected:
                heading = self._find_heading_for_id(soup, sec.id)
                if not heading:
                    continue

                markdown = self._section_to_markdown(heading, top_heading_level=1)
                result_sections.append(
                    {
                        "id": sec.id,
                        "number": sec.number,
                        "title": sec.title,
                        "length": len(markdown),
                    }
                )
                markdown_parts.append(markdown)

            # Concatenate all sections
            full_markdown = "\n\n".join(markdown_parts)

            # Extract metadata
            metadata: dict[str, Any] = {
                "url": url,
                "source": "bg3_wiki",
                "sections": result_sections,
            }

            # Add title if available
            title_tag = soup.find("title")
            if title_tag:
                metadata["title"] = title_tag.get_text(strip=True)

            # Extract character name from URL (e.g., "Astarion" from "/wiki/Astarion")
            if "/wiki/" in url:
                character_name = url.split("/wiki/")[-1]
                metadata["character_name"] = character_name

            logger.info(
                f"Successfully retrieved {len(full_markdown)} characters from {url} ({len(result_sections)} sections)"
            )

            # Extract character_name from metadata or request
            character_name = request.character_name
            return Document(
                document_id=request.document_id,
                content=full_markdown,
                metadata=metadata,
                character_name=character_name,
            )

        except requests.HTTPError as exc:
            # 404 → content not found in a business sense; other HTTP codes depend on you
            if exc.response is not None and exc.response.status_code == 404:
                logger.warning("BG3 character page not found at %s", url)
                raise ResourceNotFoundException(
                    resource_type="BG3CharacterPage",
                    resource_id=url,
                ) from exc
            # Other HTTP errors, network glitches → infra
            logger.error("HTTP error fetching URL %s: %s", url, exc)
            raise ComponentOperationException(
                component_type="source_ingestion",
                message=f"Temporary failure fetching URL {url}",
                details={"adapter": "BaldursGate3CharactersAdapter", "url": url, "status_code": exc.response.status_code if exc.response else None},
            ) from exc

        except requests.RequestException as exc:
            # Network/timeout/etc. very likely transient
            logger.error("Request exception fetching URL %s: %s", url, exc)
            raise ComponentOperationException(
                component_type="source_ingestion",
                message=f"Temporary network error fetching URL {url}",
                details={"adapter": "BaldursGate3CharactersAdapter", "url": url},
            ) from exc

        except SourceContentFormatException:
            # already a domain error, just bubble up
            raise

        except ValueError as exc:
            # e.g. _parse_top_level_toc raised because the page structure is weird
            logger.error("Section extraction error from %s: %s", url, exc)
            raise SourceContentFormatException(
                message=f"Section extraction error from {url}: {exc}",
                content_type="web",
            ) from exc

        except Exception as exc:
            # Unknown bug or unexpected HTML; treat as component error (non-retryable
            # or maybe you still mark it transient depending on your policy)
            logger.exception("Unexpected error processing content from %s: %s", url, exc)
            raise ComponentOperationException(
                component_type="source_ingestion",
                message=f"Unexpected error processing BG3 wiki page {url}",
                details={"adapter": "BaldursGate3CharactersAdapter", "url": url},
            ) from exc

    #########################################################################
    # Private helper methods
    #########################################################################

    def _fetch_html(self, url: str) -> str:
        """Download the HTML of the page.

        Args:
            url: The URL to fetch.

        Returns:
            The HTML content as a string.

        Raises:
            requests.RequestException: If the request fails.
        """
        resp = requests.get(url, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text

    def _parse_top_level_toc(self, soup: BeautifulSoup) -> list[TopSection]:
        """Parse the table of contents and return only top-level entries.

        Args:
            soup: The BeautifulSoup object.

        Returns:
            List of TopSection objects for top-level entries.
        """
        toc_div = soup.select_one("div.toc")
        if not toc_div:
            return []

        ul = toc_div.find("ul")
        if not ul:
            return []

        sections: list[TopSection] = []
        for li in ul.find_all("li", recursive=False):
            a = li.find("a")
            if not a:
                continue

            href = a.get("href")
            if not href or not isinstance(href, str) or not href.startswith("#"):
                continue

            # Standard MediaWiki structure: <span class="tocnumber">1</span> <span class="toctext">Overview</span>
            num_span = a.find("span", class_="tocnumber")
            text_span = a.find("span", class_="toctext")
            number = (num_span.get_text(strip=True) if num_span else "").strip()
            title = (text_span.get_text(strip=True) if text_span else a.get_text(strip=True)).strip()

            sections.append(TopSection(id=href[1:], number=number, title=title))

        return sections

    def _heading_level(self, tag_name: str) -> int:
        """Get numeric heading level from tag name, e.g. 'h2' -> 2.

        Args:
            tag_name: The HTML tag name.

        Returns:
            The numeric heading level, or 7 if not a heading.
        """
        if tag_name and tag_name.startswith("h") and tag_name[1:].isdigit():
            return int(tag_name[1:])
        return 7  # something bigger than any real heading

    def _find_heading_for_id(self, soup: BeautifulSoup, section_id: str) -> Tag | None:
        """Find the heading tag that corresponds to a given section id.

        MediaWiki uses: <h2><span id="Overview" class="mw-headline">Overview</span> ...</h2>
        So we find the element with that id and go up to the nearest h1–h6.

        Args:
            soup: The BeautifulSoup object.
            section_id: The section id to find.

        Returns:
            The heading tag, or None if not found.
        """
        span = soup.find(id=section_id)
        if not span:
            return None
        return span.find_parent(["h1", "h2", "h3", "h4", "h5", "h6"])

    def _clean_heading_text(self, heading_tag: Tag) -> str:
        """Remove edit links and other clutter from a heading's text.

        Args:
            heading_tag: The heading tag to clean.

        Returns:
            The cleaned heading text.
        """
        clone = copy.copy(heading_tag)
        # Delete edit-section spans if present
        for span in clone.find_all("span", class_="mw-editsection"):
            span.decompose()
        text = clone.get_text(strip=True)
        # Extra safety: drop anything starting at '[' (e.g. 'Overview[edit | edit source]')
        text = re.sub(r"\[.*$", "", text).strip()
        return text

    def _section_to_markdown(self, heading_tag: Tag, *, top_heading_level: int = 1) -> str:
        """Convert a section into clean Markdown.

        Extracts content from the heading until the next heading of same or higher level.
        Features:
        - The section title becomes H1 by default
        - Internal headings are shifted to stay relative to the new root
        - URLs are stripped; only link text is kept
        - Footnotes [1], [2], etc. and images are removed

        Args:
            heading_tag: The heading tag (e.g., <h2>Overview</h2>).
            top_heading_level: The heading level to use for the section title (default: 1).

        Returns:
            The section content as clean Markdown.
        """
        orig_level = self._heading_level(heading_tag.name)
        title = self._clean_heading_text(heading_tag)

        # Collect HTML siblings until next heading of same or higher level
        siblings = []
        for sib in heading_tag.next_siblings:
            if isinstance(sib, Tag) and sib.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                if self._heading_level(sib.name) <= orig_level:
                    break
            siblings.append(sib)

        html_fragment = "".join(str(x) for x in siblings)

        # Wrap in a dummy root so we can manipulate headings cleanly
        frag_soup = BeautifulSoup(f"<div>{html_fragment}</div>", "html.parser")
        root = frag_soup.div

        if not root:
            # Fallback if parsing fails
            body_md = md(html_fragment, heading_style="ATX", strip=["a"]).strip()
            hashes = "#" * top_heading_level
            return f"{hashes} {title}\n\n{body_md}\n"

        # 1) Normalize heading levels (so h3 -> h2, h4 -> h3, etc.,
        #    since the original h2 became our new '# Title')
        level_shift = max(0, orig_level - top_heading_level)
        if level_shift > 0:
            for lvl in range(orig_level + 1, 7):
                for h in root.find_all(f"h{lvl}"):
                    new_lvl = max(1, lvl - level_shift)
                    h.name = f"h{new_lvl}"

        # 2) Remove footnote refs (<sup>[1]</sup>) and images
        for sup in root.find_all("sup"):
            sup.decompose()
        for img in root.find_all("img"):
            img.decompose()

        # 3) Remove "Image:" links clutter
        for a in root.find_all("a"):
            if a.get_text(strip=True).startswith("Image:"):
                a.decompose()

        cleaned_html = str(root)

        # 4) Convert to Markdown, stripping <a> tags (keep their text, drop URL)
        body_md = md(
            cleaned_html,
            heading_style="ATX",
            strip=["a"],  # URLs gone, link text stays
        ).strip()

        # 5) Clean up any remaining '[edit | edit source]' or similar patterns
        body_md = re.sub(r"\[edit\s*\|\s*edit source\]", "", body_md, flags=re.IGNORECASE)
        body_md = re.sub(r"\[edit\]", "", body_md, flags=re.IGNORECASE)
        # Clean up any double spaces or extra newlines that might result
        body_md = re.sub(r" {2,}", " ", body_md)
        body_md = re.sub(r"\n{3,}", "\n\n", body_md)
        body_md = body_md.strip()

        # 6) Prepend our own heading as Markdown
        hashes = "#" * top_heading_level
        return f"{hashes} {title}\n\n{body_md}\n"

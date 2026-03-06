"""
Scrape a MAIB report page on gov.uk to extract structured metadata and download the PDF.
"""
import re
from dataclasses import dataclass
from typing import Optional

import httpx
from bs4 import BeautifulSoup


@dataclass
class ScrapedReport:
    title: str
    pdf_url: str
    pdf_bytes: bytes
    vessel_type: Optional[str]
    accident_date: Optional[str]
    accident_location: Optional[str]
    publication_date: Optional[str]


def scrape(url: str) -> ScrapedReport:
    """Fetch a MAIB report page and download the attached PDF.

    Raises ValueError if the page doesn't look like a valid MAIB report page.
    Raises httpx.HTTPError on network failures.
    """
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        page = client.get(url)
        page.raise_for_status()

    soup = BeautifulSoup(page.text, "html.parser")

    title = _extract_title(soup)
    pdf_url = _extract_pdf_url(soup)
    if not pdf_url:
        raise ValueError(f"No PDF attachment found on page: {url}")

    metadata = _extract_metadata(soup)

    with httpx.Client(follow_redirects=True, timeout=60) as client:
        pdf_response = client.get(pdf_url)
        pdf_response.raise_for_status()

    return ScrapedReport(
        title=title,
        pdf_url=pdf_url,
        pdf_bytes=pdf_response.content,
        vessel_type=metadata.get("vessel_type"),
        accident_date=metadata.get("accident_date"),
        accident_location=metadata.get("accident_location"),
        publication_date=metadata.get("publication_date"),
    )


def _extract_title(soup: BeautifulSoup) -> str:
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        return og_title["content"].strip()
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else ""


def _extract_pdf_url(soup: BeautifulSoup) -> Optional[str]:
    """Find the first PDF link inside an attachment-inline span."""
    attachment = soup.select_one("span.attachment-inline a[href]")
    if attachment:
        href = attachment["href"]
        if href.endswith(".pdf"):
            return href
    # Fallback: any link to assets.publishing.service.gov.uk ending in .pdf
    for a in soup.find_all("a", href=True):
        if "assets.publishing.service.gov.uk" in a["href"] and a["href"].endswith(".pdf"):
            return a["href"]
    return None


def _extract_metadata(soup: BeautifulSoup) -> dict:
    """Extract vessel_type, accident_date, accident_location, publication_date."""
    result = {}

    # vessel_type, accident_date — from gem-c-metadata dl
    terms = soup.select("dt.gem-c-metadata__term")
    for dt in terms:
        label = dt.get_text(strip=True).rstrip(":").lower()
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue
        value = dd.get_text(strip=True)
        if not value:
            continue

        if label == "vessel type":
            result["vessel_type"] = value
        elif label == "date of occurrence":
            result["accident_date"] = value

    # accident_location — og:description contains "Location: ..."
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        m = re.match(r"Location:\s*(.+)", og_desc["content"].strip())
        if m:
            result["accident_location"] = m.group(1).rstrip(".")

    # publication_date — govuk:first-published-at meta tag (ISO 8601)
    pub_meta = soup.find("meta", attrs={"name": "govuk:first-published-at"})
    if pub_meta and pub_meta.get("content"):
        # e.g. "2025-05-14T23:58:41+01:00" → "2025-05-14"
        result["publication_date"] = pub_meta["content"][:10]

    return result

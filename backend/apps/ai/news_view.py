"""
News feed endpoint — aggregates RSS from supply chain, AI, and tech sources.
Cached in Redis for 30 minutes so we don't hammer upstream feeds.
"""
import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

FEEDS = [
    {
        "source": "Supply Chain Dive",
        "tag": "supply-chain",
        "url": "https://www.supplychaindive.com/feeds/news/",
        "color": "#0D9488",
    },
    {
        "source": "Logistics Management",
        "tag": "supply-chain",
        "url": "https://www.logisticsmgmt.com/rss/all",
        "color": "#0D9488",
    },
    {
        "source": "MIT Tech Review",
        "tag": "technology",
        "url": "https://www.technologyreview.com/feed/",
        "color": "#6366F1",
    },
    {
        "source": "VentureBeat AI",
        "tag": "ai",
        "url": "https://venturebeat.com/category/ai/feed/",
        "color": "#8B5CF6",
    },
    {
        "source": "The Verge",
        "tag": "technology",
        "url": "https://www.theverge.com/rss/index.xml",
        "color": "#F59E0B",
    },
]

NS = {"atom": "http://www.w3.org/2005/Atom"}


def _parse_rss(xml_text: str, source: str, tag: str, color: str) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_text)
        # RSS 2.0
        for item in root.findall(".//item")[:4]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            desc = (item.findtext("description") or "").strip()
            if title and link:
                items.append({"title": title, "url": link, "pub": pub, "summary": desc[:120], "source": source, "tag": tag, "color": color})
    except ET.ParseError:
        pass
    # Atom fallback
    if not items:
        try:
            root = ET.fromstring(xml_text)
            for entry in root.findall("atom:entry", NS)[:4]:
                title = (entry.findtext("atom:title", namespaces=NS) or "").strip()
                link_el = entry.find("atom:link", NS)
                link = link_el.get("href", "") if link_el is not None else ""
                pub = (entry.findtext("atom:updated", namespaces=NS) or "").strip()
                summary = (entry.findtext("atom:summary", namespaces=NS) or "").strip()
                if title and link:
                    items.append({"title": title, "url": link, "pub": pub, "summary": summary[:120], "source": source, "tag": tag, "color": color})
        except ET.ParseError:
            pass
    return items


def fetch_news() -> list[dict]:
    cache_key = "hrms:news_feed:v1"
    cached = cache.get(cache_key)
    if cached:
        return cached

    all_articles: list[dict] = []
    for feed in FEEDS:
        try:
            resp = requests.get(feed["url"], timeout=5, headers={"User-Agent": "HRMS-AI/1.0"})
            if resp.ok:
                articles = _parse_rss(resp.text, feed["source"], feed["tag"], feed["color"])
                all_articles.extend(articles)
        except Exception as exc:
            logger.warning("News feed fetch failed for %s: %s", feed["source"], exc)

    # Sort by source order (preserves diversity); limit 20
    result = all_articles[:20]
    if result:
        cache.set(cache_key, result, timeout=1800)  # 30 min
    return result


class NewsFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tag = request.query_params.get("tag")
        articles = fetch_news()
        if tag:
            articles = [a for a in articles if a["tag"] == tag]
        return Response({"articles": articles, "fetched_at": int(time.time())})

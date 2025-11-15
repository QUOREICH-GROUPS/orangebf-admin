import scrapy
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


class OrangeServicesSpider(scrapy.Spider):
    name = "orange_services"
    allowed_domains = ["orange.bf"]
    start_urls = [
        "https://www.orange.bf/fr/les-service-et-offres-mobile.html",
        "https://www.orange.bf/fr/catalogue/services-mobile.html",
        "https://www.orange.bf/fr/assistance.html",
        "https://www.orange.bf/fr/assistance/orange-energie/assistance-orange-energie.html",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "AUTOTHROTTLE_ENABLED": True,
        "ROBOTSTXT_OBEY": True,
        "USER_AGENT": "HumanoidAssistantBot (+https://github.com/abdouramane-sawadogo)",
        "FEEDS": {
            "orange_services.json": {"format": "json", "encoding": "utf8"},
        },
        "LOG_LEVEL": "DEBUG",
    }

    def parse(self, response):
        soup = BeautifulSoup(response.text, "lxml")

        # Supprimer les scripts, styles, menus, etc.
        for s in soup(["script", "style", "noscript", "footer", "header", "nav", "form"]):
            s.decompose()

        # Nettoyage du texte
        text = " ".join(soup.stripped_strings)
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) > 100:
            yield {
                "url": response.url,
                "type": "page",
                "content": text,
            }

        # Suivre uniquement les liens internes aux mêmes sections
        for href in response.css("a::attr(href)").getall():
            full_url = urljoin(response.url, href)
            if (
                self.allowed_domains[0] in full_url
                and not full_url.endswith(".pdf")
                and not any(x in full_url for x in ["#", "mailto:", "tel:"])
                and (
                    "/fr/assistance" in full_url
                    or "/fr/catalogue" in full_url
                    or "/fr/les-service-et-offres-mobile" in full_url
                )
            ):
                yield scrapy.Request(full_url, callback=self.parse)

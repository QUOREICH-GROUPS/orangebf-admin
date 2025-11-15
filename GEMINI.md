# Project Overview

This project is a Scrapy-based web scraper designed to extract information about services and offers from the Orange Burkina Faso website (orange.bf). It navigates through predefined URLs, extracts textual content from pages, and downloads associated PDF files.

## Main Technologies

*   **Python:** The core programming language.
*   **Scrapy:** The web scraping framework used to build the spider.
*   **BeautifulSoup:** Used for parsing and cleaning HTML content.

## Project Structure

*   `scrapy.cfg`: The Scrapy project configuration file.
*   `orange_scraper/`: The main Python package for the Scrapy project.
    *   `__init__.py`: Initializes the Python package.
    *   `items.py`: Defines the data containers for scraped data (Scrapy Items).
    *   `middlewares.py`: Defines Scrapy Middlewares for custom processing of requests and responses.
    *   `pipelines.py`: Defines Scrapy Pipelines for processing scraped items (e.g., saving to a database, downloading files).
    *   `settings.py`: Project-specific settings for the Scrapy spider.
    *   `spiders/`: Directory containing the Scrapy spiders.
        *   `orange_spider.py`: Contains the primary spider logic. This spider, named "orange_services," is responsible for crawling the website, parsing HTML, extracting data, and identifying PDF files for download.
*   `elasticsearch_manager.py`: A placeholder for managing Elasticsearch interactions.
*   `index_data.py`: A script to load scraped data from `orange_services.json` and index it into Elasticsearch.

## How it Works

The `orange_services` spider starts by visiting a set of initial URLs specified in `start_urls`. For each page it visits, it performs the following actions:

1.  **HTML Parsing:** It uses BeautifulSoup to parse the HTML, removing irrelevant elements like scripts, styles, headers, and footers.
2.  **Text Extraction:** It extracts and cleans the textual content from the page. If the content is substantial, it is saved along with the URL.
3.  **PDF Extraction:** It finds all links ending with `.pdf` and sends requests to download them using Scrapy's built-in `FilesPipeline`.
4.  **Crawling:** It identifies and follows internal links that are relevant to the scraping target, ensuring it stays within the service and assistance sections of the website.

## Output

*   **JSON Data:** Extracted page content is saved to `orange_services.json`. Each entry includes the URL, content type (`page`), and the extracted text.
*   **PDF Files:** Downloaded PDF files are stored in the `./pdfs` directory.

# Building and Running

To run the scraper, you need to have Scrapy installed (`pip install scrapy`).

## Running the Spider

You can run the spider using the following command from the project's root directory:

```bash
scrapy crawl orange_services
```

This command will start the scraping process. The output will be a file named `orange_services.json` in the root directory, and the downloaded PDFs will be in the `pdfs` directory.

## Indexing Scraped Data

To index the `orange_services.json` data into Elasticsearch, run the `index_data.py` script:

```bash
python index_data.py
```

Ensure your Elasticsearch instance is running and accessible at the configured host.

# Development Conventions

*   **User-Agent:** The spider uses a custom User-Agent (`HumanoidAssistantBot`) to identify itself.
*   **Throttling:** The scraper is configured with a download delay and autothrottling to avoid overloading the server.
*   **Logging:** The log level is set to `INFO` for concise output.

# Plan to Scrap More Data

To expand the data scraping from `orange.bf`, follow these steps:

1.  **Explore `orange.bf` for new data sources:** Manually browse the website to identify new sections (e.g., news, promotions, product catalog) that contain valuable information not currently being scraped.
2.  **Update `orange_scraper/spiders/orange_spider.py`:**
    *   Add more URLs to the `start_urls` list to cover the newly identified sections.
    *   Modify the `parse` method to handle the HTML structure of these new pages. This might involve adding new CSS selectors or XPath expressions to extract relevant data.
    *   Consider adding logic to follow pagination links if new sections have multiple pages.
3.  **Define new Scrapy Items (if necessary):** If the new data types are significantly different from the current "page content" and "pdf" types, create new Item classes in `orange_scraper/items.py` to define their structure (e.g., `ProductItem`, `NewsArticleItem`).
4.  **Implement new Pipelines (if necessary):** If the new Items require specific processing (e.g., image downloads, database storage, custom data cleaning), create new Item Pipelines in `orange_scraper/pipelines.py`.
5.  **Adjust `orange_scraper/settings.py`:** Update `ITEM_PIPELINES` to activate new pipelines, and potentially adjust `DOWNLOAD_DELAY`, `USER_AGENT`, or `ROBOTSTXT_OBEY` if the new scraping targets require different behavior.

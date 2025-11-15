BOT_NAME = "orange_scraper"

SPIDER_MODULES = ["orange_scraper.spiders"]
NEWSPIDER_MODULE = "orange_scraper.spiders"

ROBOTSTXT_OBEY = True
AUTOTHROTTLE_ENABLED = True
DOWNLOAD_DELAY = 1.0

# ITEM_PIPELINES = {
#     "scrapy.pipelines.files.FilesPipeline": 1,
# }

# FILES_STORE = "./pdfs"
LOG_LEVEL = "INFO"
USER_AGENT = "HumanoidAssistantBot (+https://github.com/abdouramane-sawadogo)"

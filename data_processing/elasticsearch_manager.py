import logging
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ConnectionError, NotFoundError, RequestError

logger = logging.getLogger(__name__)

class ElasticsearchManager:
    def __init__(self, hosts=None, username=None, password=None, api_key=None):
        logger.info("Initializing ElasticsearchManager")
        self.hosts = hosts
        self.username = username
        self.password = password
        self.api_key = api_key
        self.es = None
        try:
            auth_params = {}
            if self.api_key:
                auth_params["api_key"] = self.api_key
            elif self.username and self.password:
                auth_params["basic_auth"] = (self.username, self.password)

            self.es = Elasticsearch(
                hosts=self.hosts,
                **auth_params,
                verify_certs=False # Consider setting to True in production with proper CA certs
            )
            # Ping to check connection
            if not self.es.ping():
                raise ConnectionError("Could not connect to Elasticsearch!")
            logger.info("Successfully connected to Elasticsearch.")
        except ConnectionError as e:
            logger.error(f"Elasticsearch Connection Error: {e}")
            self.es = None
        except Exception as e:
            logger.error(f"An unexpected error occurred during Elasticsearch initialization: {e}")
            self.es = None

    def create_index(self, index_name):
        if not self.es:
            logger.error("Elasticsearch client not initialized. Cannot create index.")
            return False
        try:
            if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name)
                logger.info(f"Index '{index_name}' created successfully.")
            else:
                logger.info(f"Index '{index_name}' already exists.")
            return True
        except RequestError as e:
            if e.error == 'resource_already_exists_exception':
                logger.warning(f"Index '{index_name}' already exists.")
                return True
            logger.error(f"Error creating index '{index_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while creating index '{index_name}': {e}")
            return False

    def bulk_index_documents(self, index_name, documents, refresh=False):
        if not self.es:
            logger.error("Elasticsearch client not initialized. Cannot bulk index documents.")
            return 0
        try:
            # The documents list should already be in the format expected by helpers.bulk
            # e.g., [{"_index": "my_index", "_source": {"field": "value"}}]
            success, failed = helpers.bulk(self.es, documents, index=index_name, refresh=refresh)
            if failed:
                logger.warning(f"Failed to index {len(failed)} documents.")
            logger.info(f"Successfully indexed {success} documents into index: {index_name}")
            return success
        except Exception as e:
            logger.error(f"An error occurred during bulk indexing: {e}")
            return 0
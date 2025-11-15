import json
import logging
import os
from elasticsearch_manager import ElasticsearchManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def index_orange_services(es_manager, index_name, json_file):
    """
    Loads data from a JSON file and indexes it into Elasticsearch.

    :param es_manager: An instance of ElasticsearchManager.
    :param index_name: The name of the Elasticsearch index.
    :param json_file: The path to the JSON file containing the data.
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Error: The file {json_file} was not found.")
        return
    except json.JSONDecodeError:
        logger.error(f"Error: Could not decode JSON from the file {json_file}.")
        return

    if not data:
        logger.warning("The JSON file is empty. No data to index.")
        return

    # Assuming the JSON file contains a list of documents
    documents = []
    for item in data:
        # Ensure the document has an _id for idempotency if desired,
        # or let Elasticsearch generate one. For now, let's let ES generate.
        documents.append({
            "_source": item,
        })

    logger.info(f"Indexing {len(documents)} documents from {json_file} into index {index_name}")
    es_manager.bulk_index_documents(index_name, documents, refresh=True)
    logger.info("Data indexing complete.")

if __name__ == "__main__":
    # Get Elasticsearch connection details from environment variables
    es_hosts_str = os.getenv("ES_HOSTS", "https://9ce0d46a529144858720414e2ba0586e.us-central1.gcp.cloud.es.io:443")
    es_api_key = os.getenv("ES_API_KEY", "ZVg2cWVab0JVQVQ3TTVEVjI4bTQ6cl9IczgtYkNaQmRDMG1rMzgycm5hUQ==")

    es_hosts = [host.strip() for host in es_hosts_str.split(',')]

    # Initialize ElasticsearchManager
    es_manager = ElasticsearchManager(
        hosts=es_hosts,
        api_key=es_api_key
    )

    # Define the index name and the path to the JSON file
    index_name = "orange_services"
    json_file_path = "orange_services_clean.json"

    # Only proceed if ElasticsearchManager was successfully initialized
    if es_manager.es:
        # Create the index if it doesn't exist
        if es_manager.create_index(index_name):
            # Index the data
            index_orange_services(es_manager, index_name, json_file_path)
        else:
            logger.error(f"Could not create or ensure existence of index {index_name}. Aborting indexing.")
    else:
        logger.error("ElasticsearchManager failed to initialize. Please check your connection details.")
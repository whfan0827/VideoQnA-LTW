import logging

import chromadb
from chromadb.api import ClientAPI

from .prompt_content_db import nonewlines, PromptContentDB, VECTOR_FIELD_NAME
from vi_search.constants import CHROMA_DB_DIR


logger = logging.getLogger(__name__)


class ChromaDB(PromptContentDB):
    def __init__(self, persist_directory=None) -> None:
        '''
        :param persist_directory: The directory where the collection will be stored
        '''
        super().__init__()

        # Create a new Chroma client with persistence enabled
        self._persist_directory = persist_directory or CHROMA_DB_DIR
        path = str(self._persist_directory)
        print(f"ChromaDB: Using persist directory: {path}")
        self.client: ClientAPI = chromadb.PersistentClient(path=path)

    def create_db(self, name: str, vector_search_dimensions: int) -> None:
        ''' Create new or get existing chromadb collection.

        :param name: The name of the collection
        :param vector_search_dimensions: The number of dimensions of the embeddings (unused in ChromaDB)
        '''
        collection = self.client.get_or_create_collection(name)
        self.db_name = name
        self.db_handle = collection

    def remove_db(self, name: str) -> None:
        """ Removes collection. """
        collections = self.client.list_collections()
        for collection in collections:
            if collection.name == name:
                self.client.delete_collection(name)
                print(f"Collection {name} deleted")
                return

        print(f"Collection {name} not found")

    def get_available_dbs(self) -> list[str]:
        ''' Get the list of available collections. '''
        collections = self.client.list_collections()
        collection_names = [collection.name for collection in collections]
        return collection_names

    def set_db(self, name: str) -> None:
        collection = self.client.get_collection(name)
        self.db_name = name
        self.db_handle = collection

    def add_entry_batch(self, entry_batch):
        ''' Add entry batch to the collection.

        :param entry_batch: List of entries to be added to the collection
        '''
        data = self._transform_sections_to_chromadb_format(entry_batch)
        self.db_handle.add(**data)

    @staticmethod
    def _transform_sections_to_chromadb_format(batch):
        """ Pivot sections into a format suitable for chromadb. """

        ids = []
        documents = []
        embeddings = []
        metadatas = []
        for s in batch:
            ids.append(s.pop('id'))
            documents.append(s.pop('content'))
            embeddings.append(s.pop(VECTOR_FIELD_NAME))
            metadatas.append(s)

        data = {
            'ids': ids,
            'documents': documents,
            'embeddings': embeddings,
            'metadatas': metadatas
        }

        return data

    def vector_search(self, embeddings_vector, n_results=3) -> tuple[dict, list[str]]:
        ''' Query the collection with the given embeddings vector.

        :param embeddings_vector: embeddings vector to search in the collection
        :param n_results: Number of results to return
        '''
        results = self.db_handle.query(query_embeddings=[embeddings_vector], n_results=n_results)

        docs_by_id = {}
        results_content = []
        if results.get('ids') and len(results['ids']) > 0:
            for idx, uid in enumerate(results['ids'][0]):
                metadata_list = results.get('metadatas', [[]])
                documents_list = results.get('documents', [[]])
                distances_list = results.get('distances', [[]])
                
                # Safely access the first element of each list
                metadata = metadata_list[0] if metadata_list and len(metadata_list) > 0 else []
                documents = documents_list[0] if documents_list and len(documents_list) > 0 else []
                distances = distances_list[0] if distances_list and len(distances_list) > 0 else []
                
                if idx < len(metadata):
                    docs_by_id[uid] = metadata[idx] or {}
                    if idx < len(documents):
                        docs_by_id[uid].update({'content': documents[idx] or ''})
                    if idx < len(distances):
                        docs_by_id[uid].update({'distance': distances[idx] or 0.0})
                    results_content.append(f'{uid}: {nonewlines(documents[idx] if idx < len(documents) else "")}')

        return docs_by_id, results_content

    def get_collection_data(self):
        ''' Get collection's data. '''

        all_data = self.db_handle.get(include=['embeddings', 'documents', 'metadatas'])
        return all_data

    def delete_video_documents(self, video_id: str) -> bool:
        """
        Delete all documents belonging to a specific video from the collection.
        
        :param video_id: The video ID to delete documents for
        :return: True if deletion was successful, False otherwise
        """
        try:
            # Get all documents with the specific video_id
            all_data = self.db_handle.get(include=['metadatas'])
            
            metadatas = all_data.get('metadatas')
            if not metadatas:
                logger.warning(f"No metadata found in collection")
                return False
            
            # Find IDs that match the video_id
            ids_to_delete = []
            for idx, metadata in enumerate(metadatas):
                if metadata and metadata.get('video_id') == video_id:
                    ids_to_delete.append(all_data['ids'][idx])
            
            if ids_to_delete:
                # Delete the documents
                self.db_handle.delete(ids=ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} documents for video {video_id}")
                return True
            else:
                logger.warning(f"No documents found for video {video_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete documents for video {video_id}: {e}")
            return False

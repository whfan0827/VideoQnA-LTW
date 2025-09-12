import logging
from typing import List

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
        if results and results.get('ids') and len(results['ids']) > 0:
            documents = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            for idx, uid in enumerate(results['ids'][0]):
                doc = {
                    'id': uid,
                    'content': documents[idx] if documents and idx < len(documents) else "",
                    **(metadatas[idx] if metadatas and idx < len(metadatas) else {})
                }
                docs_by_id[uid] = doc
                results_content.append(f'{uid}: {nonewlines(doc["content"])}')

        return docs_by_id, results_content

    def get_existing_video_ids(self, db_name: str, video_ids: List[str]) -> List[str]:
        """
        Given a list of video_ids, return the subset of those that already exist in the specified ChromaDB collection.
        
        :param db_name: The name of the collection to check.
        :param video_ids: A list of video IDs to check for existence.
        :return: A list of video IDs that are already present in the collection.
        """
        if not video_ids:
            return []

        try:
            collection = self.client.get_collection(db_name)
            
            # For ChromaDB, we need to check each video_id individually due to the filter limitations
            existing_ids = []
            
            for video_id in video_ids:
                try:
                    # Query for documents with this specific video_id
                    results = collection.get(
                        where={"video_id": video_id},
                        include=["metadatas"],
                        limit=1
                    )
                    
                    # If we got results, this video_id exists
                    metadatas = results.get('metadatas') if results else None
                    if metadatas and len(metadatas) > 0:
                        existing_ids.append(video_id)
                        
                except Exception as e:
                    logger.warning(f"Error checking video_id {video_id} in collection '{db_name}': {e}")
                    continue
            
            logger.info(f"Checked for {len(video_ids)} video IDs in collection '{db_name}', found {len(existing_ids)} existing.")
            return existing_ids

        except Exception as e:
            logger.error(f"Failed to get existing video IDs from collection '{db_name}': {e}")
            return []

    def delete_video_documents(self, video_id: str) -> bool:
        """
        Delete all documents belonging to a specific video from the ChromaDB collection.
        
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

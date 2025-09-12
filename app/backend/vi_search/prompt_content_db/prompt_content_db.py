from abc import ABC, abstractmethod
import logging
from typing import List


logger = logging.getLogger(__name__)

VECTOR_FIELD_NAME = "content_vector"



class PromptContentDB(ABC):
    def __init__(self) -> None:
        self.db_name = None
        self.db_handle = None

    @abstractmethod
    def create_db(self, name: str, vector_search_dimensions: int) -> None:
        pass

    @abstractmethod
    def remove_db(self, name: str) -> None:
        pass

    @abstractmethod
    def get_available_dbs(self) -> list[str]:
        pass

    @abstractmethod
    def set_db(self, name: str) -> None:
        pass

    @abstractmethod
    def add_entry_batch(self, entry_batch):
        pass

    def add_sections_to_db(self, sections, upload_batch_size=100, verbose=False):
        logger.info(f"Adding sections into DB '{self.db_name}'...")

        # TODO: Consider adding parallelism here.
        #       Notice that `sections` is a generator which actually does LLM inferences on the fly
        i = 0
        batch = []
        for s in sections:
            if verbose:
                print(s)

            batch.append(s)
            i += 1
            if i % upload_batch_size == 0:
                logger.info(f"Uploading batch {i} from {s['video_name']} into DB {self.db_name}")
                self.add_entry_batch(batch)
                batch = []

        logger.debug(f"Batch Length: {len(batch)}")

        if len(batch) > 0:
            self.add_entry_batch(batch)

        logger.info(f"Finished storing {i} sections into DB {self.db_name}'")

    @abstractmethod
    def vector_search(self, embeddings_vector, n_results=3) -> tuple[dict, list[str]]:
        ''' Search for the `n_results` closest embeddings to the given vector. '''
        pass

    @abstractmethod
    def get_existing_video_ids(self, db_name: str, video_ids: List[str]) -> List[str]:
        """
        Given a list of video_ids, return the subset of those that already exist in the specified DB.
        
        :param db_name: The name of the database (index) to check.
        :param video_ids: A list of video IDs to check for existence.
        :return: A list of video IDs that are already present in the database.
        """
        pass

    @abstractmethod
    def delete_video_documents(self, video_id: str) -> bool:
        """
        Delete all documents belonging to a specific video from the database.
        
        :param video_id: The video ID to delete documents for
        :return: True if deletion was successful, False otherwise
        """
        pass


def nonewlines(s: str) -> str:
    return s.replace('\n', ' ').replace('\r', ' ')

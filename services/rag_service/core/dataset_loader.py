"""
Hugging Face Dataset Loader.

Streams datasets from Hugging Face Hub and ingests them into the FactStore.
"""
import asyncio
from typing import AsyncGenerator, Any

from shared.schemas import AtomicFact
from shared.logging import get_logger

logger = get_logger(__name__)

class DatasetLoader:
    def __init__(self):
        try:
            import datasets
            self._datasets = datasets
            # Disable caching to save disk space for large crawls
            self._datasets.disable_caching()
        except ImportError:
            logger.error("datasets library not found. Install with `pip install datasets`")
            raise

    async def stream_dataset(
        self, 
        dataset_name: str, 
        split: str = "train", 
        max_rows: int = 1000,
        mapping: dict[str, str] = None
    ) -> AsyncGenerator[AtomicFact, None]:
        """
        Stream a dataset from HF and yield AtomicFacts.
        
        Args:
            dataset_name: HF dataset ID (e.g. "wikipedia")
            split: Dataset split
            max_rows: Limit rows to ingest
            mapping: Map dataset columns to AtomicFact fields
                     {"text_col": "value", "title_col": "entity", ...}
        """
        # Default mapping if none provided - tries to be smart
        if not mapping:
            mapping = {
                "text": "value",
                "content": "value", 
                "title": "entity",
                "url": "source_url"
            }

        logger.info(f"Streaming dataset {dataset_name} [{split}] (max: {max_rows})...")
        
        try:
            # Load dataset in streaming mode (IterableDataset)
            ds = self._datasets.load_dataset(dataset_name, split=split, streaming=True)
            
            count = 0
            for row in ds:
                if count >= max_rows:
                    break
                
                # Extract fields based on mapping
                value = row.get(mapping.get("value") or "text", "")
                if not value: continue # Skip empty rows
                
                # Truncate value to avoid vector store limits
                value = str(value)[:2000]

                entity = row.get(mapping.get("entity") or "title", "Unknown Entity")
                source_url = row.get(mapping.get("source_url") or "url", f"hf://{dataset_name}")
                
                # Create rudimentary fact
                # For basic text datasets, the entire text is the "value", 
                # and the attribute is effectively "content".
                fact = AtomicFact(
                    fact_id=f"hf-{dataset_name}-{count}", 
                    entity=str(entity)[:100],
                    attribute="content", # Generic attribute for raw text
                    value=value,
                    source_url=str(source_url),
                    source_title=f"{dataset_name}",
                    confidence_score=1.0 # It's a gold dataset usually
                )
                
                yield fact
                count += 1
                
                # Yield control to event loop every 10 rows to prevent blocking
                if count % 10 == 0:
                    await asyncio.sleep(0)

            logger.info(f"Finished streaming {count} rows from {dataset_name}")

        except Exception as e:
            logger.error(f"Failed to stream dataset {dataset_name}: {e}")
            raise

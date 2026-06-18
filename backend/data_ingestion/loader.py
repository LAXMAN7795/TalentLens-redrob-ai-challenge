import json
import logging
from typing import Generator, Dict, Any, Union
from pathlib import Path

# Set up logger
logger = logging.getLogger(__name__)

class CandidateLoader:
    """
    A memory-efficient streaming loader for candidate profiles in JSONL format.
    Streams records line-by-line rather than loading everything into memory.
    """
    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)

    def stream_raw_records(self) -> Generator[Dict[str, Any], None, None]:
        """
        Reads the JSONL file line-by-line and yields the raw dictionaries.
        Skipping malformed rows while logging warnings.
        """
        if not self.file_path.exists():
            logger.error(f"Target data file not found: {self.file_path}")
            raise FileNotFoundError(f"Candidate profiles file not found: {self.file_path}")
        
        logger.info(f"Starting candidate ingestion stream from: {self.file_path}")
        
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                for line_num, line in enumerate(file, start=1):
                    stripped_line = line.strip()
                    if not stripped_line:
                        continue
                    try:
                        yield json.loads(stripped_line)
                    except json.JSONDecodeError as exc:
                        logger.warning(
                            f"Skipping malformed JSON on line {line_num} of {self.file_path.name}: {exc}"
                        )
        except Exception as exc:
            logger.critical(f"Error occurred during streaming read of {self.file_path}: {exc}")
            raise
        
        logger.info(f"Finished candidate ingestion stream from: {self.file_path}")

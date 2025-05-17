#!/usr/bin/env python3
"""
Unified file handling utilities for the newsletter system.
"""
import json
import re
from enum import Enum, auto
from pathlib import Path
from typing import Union, Dict, List, Tuple, Optional

from .logger_config import get_logger, get_module_name


class FileType(Enum):
    """Enum for different types of files in the system."""
    # News related files
    ARTICLES = auto()  # News articles
    ARTICLE_GROUPS = auto()  # Grouped articles

    # Newsletter related files
    UNPROCESSED_NEWSLETTER = auto()  # Raw newsletter before processing
    PROCESSED_NEWSLETTER = auto()  # Newsletter after processing
    FORMATTED_NEWSLETTER = auto()  # Final formatted newsletter HTML

    # Prompt related files
    PROMPT = auto()  # Prompt templates

    # Other files
    TEXT = auto()  # Generic text files
    JSON = auto()  # Generic JSON files


class FileCategory(Enum):
    """Enum for different categories of files in the system."""
    NEWS = auto()  # News related files
    NEWSLETTER = auto()  # Newsletter related files
    PROMPT = auto()  # Prompt related files
    OTHER = auto()  # Other files


class FileHandler:
    """Unified file handling class for the newsletter system."""

    # Directory structure mapping
    DIRECTORIES = {
        FileType.ARTICLES: "src/outputs/news/articles",
        FileType.ARTICLE_GROUPS: "src/outputs/news/article_groups",
        FileType.UNPROCESSED_NEWSLETTER: "src/outputs/newsletters/unprocessed",
        FileType.PROCESSED_NEWSLETTER: "src/outputs/newsletters/processed",
        FileType.FORMATTED_NEWSLETTER: "src/outputs/newsletters/formatted",
        FileType.PROMPT: "src/prompts",
        FileType.TEXT: "src/outputs/text",
        FileType.JSON: "src/outputs/json"
    }

    # File type to category mapping
    TYPE_TO_CATEGORY = {
        FileType.ARTICLES: FileCategory.NEWS,
        FileType.ARTICLE_GROUPS: FileCategory.NEWS,
        FileType.UNPROCESSED_NEWSLETTER: FileCategory.NEWSLETTER,
        FileType.PROCESSED_NEWSLETTER: FileCategory.NEWSLETTER,
        FileType.FORMATTED_NEWSLETTER: FileCategory.NEWSLETTER,
        FileType.PROMPT: FileCategory.PROMPT,
        FileType.TEXT: FileCategory.OTHER,
        FileType.JSON: FileCategory.OTHER
    }

    # File type to extension mapping
    TYPE_TO_EXTENSION = {
        FileType.ARTICLES: ".json",
        FileType.ARTICLE_GROUPS: ".json",
        FileType.UNPROCESSED_NEWSLETTER: ".json",
        FileType.PROCESSED_NEWSLETTER: ".json",
        FileType.FORMATTED_NEWSLETTER: ".html",
        FileType.PROMPT: ".txt",
        FileType.TEXT: ".txt",
        FileType.JSON: ".json"
    }

    def __init__(self):
        """Initialize the FileHandler with logger."""
        self.logger = get_logger(get_module_name(__name__))

    def _get_file_path(self, file_type: FileType, date_str: Optional[str] = None,
                       base_name: Optional[str] = None) -> Path:
        """Get the full file path based on type and date.

        Args:
            file_type (FileType): Type of file to handle
            date_str (Optional[str]): Date string in YYYY-MM-DD format
            base_name (Optional[str]): Base name for the file

        Returns:
            Path: Full path to the file
        """
        directory = Path(self.DIRECTORIES[file_type])
        extension = self.TYPE_TO_EXTENSION[file_type]

        if date_str:
            if base_name:
                filename = f"{base_name}_{date_str}{extension}"
            else:
                # Special case for formatted newsletters
                if file_type == FileType.FORMATTED_NEWSLETTER:
                    filename = f"newsletter_formatted_{date_str}{extension}"
                else:
                    filename = f"{file_type.name.lower()}_{date_str}{extension}"
        else:
            filename = f"{base_name or file_type.name.lower()}{extension}"

        return directory / filename

    def load_file(self, file_type: FileType, date_str: Optional[str] = None,
                  base_name: Optional[str] = None, encoding: str = 'utf-8') -> Union[Dict, List, str]:
        """Load a file based on its type.

        Args:
            file_type (FileType): Type of file to load
            date_str (Optional[str]): Date string in YYYY-MM-DD format
            base_name (Optional[str]): Base name for the file
            encoding (str): File encoding to use

        Returns:
            Union[Dict, List, str]: Loaded file content

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If content is invalid
        """
        try:
            file_path = self._get_file_path(file_type, date_str, base_name)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Load text files (including prompts) as plain text
            if file_type in [FileType.FORMATTED_NEWSLETTER, FileType.TEXT, FileType.PROMPT]:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
            else:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = json.load(f)

            self.logger.info("Loaded file from: %s", file_path)
            return content

        except Exception as e:
            self.logger.error(
                "Error loading file from %s: %s", file_path, str(e))
            raise

    def save_file(self, content: Union[Dict, List, str], file_type: FileType,
                  date_str: Optional[str] = None, base_name: Optional[str] = None,
                  encoding: str = 'utf-8', ensure_ascii: bool = False,
                  indent: int = 2) -> Path:
        """Save content to a file based on its type.

        Args:
            content: Content to save
            file_type (FileType): Type of file to save
            date_str (Optional[str]): Date string in YYYY-MM-DD format
            base_name (Optional[str]): Base name for the file
            encoding (str): File encoding to use
            ensure_ascii (bool): Whether to ensure ASCII output for JSON
            indent (int): Number of spaces for JSON indentation

        Returns:
            Path: Path to the saved file

        Raises:
            ValueError: If content is invalid
            IOError: If file cannot be written
        """
        file_path = None
        try:
            file_path = self._get_file_path(file_type, date_str, base_name)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if file_type in [FileType.FORMATTED_NEWSLETTER, FileType.TEXT, FileType.PROMPT]:
                if not isinstance(content, str):
                    raise ValueError("Content must be a string for text files")
                with open(file_path, 'w', encoding=encoding) as f:
                    f.write(content)
            else:
                if not isinstance(content, (dict, list)):
                    raise ValueError(
                        "Content must be a dictionary or list for JSON files")
                with open(file_path, 'w', encoding=encoding) as f:
                    json.dump(content, f, ensure_ascii=ensure_ascii,
                              indent=indent)

            self.logger.info("Saved file to: %s", file_path)
            return file_path

        except Exception as e:
            error_msg = f"Error saving file{f' to {file_path}' if file_path else ''}: {str(e)}"
            self.logger.error(error_msg)
            raise

    def find_latest_file(self, file_type: FileType, pattern: Optional[str] = None) -> Optional[Path]:
        """Find the most recent file of a given type.

        Args:
            file_type (FileType): Type of file to find
            pattern (Optional[str]): Additional pattern to match

        Returns:
            Optional[Path]: Path to the most recent file, or None if no files found
        """
        try:
            directory = Path(self.DIRECTORIES[file_type])
            if not directory.exists():
                raise FileNotFoundError(f"Directory not found: {directory}")

            if pattern:
                search_pattern = pattern
            else:
                extension = self.TYPE_TO_EXTENSION[file_type]
                search_pattern = f"*{extension}"

            files = list(directory.glob(search_pattern))
            if not files:
                return None

            return max(files, key=lambda x: x.stat().st_mtime)

        except Exception as e:
            self.logger.error(
                "Error finding latest file in %s: %s", directory, str(e))
            raise

    def extract_date_from_filename(self, filename: Union[str, Path]) -> Tuple[Optional[str], Optional[int]]:
        """Extract date and increment from a filename.

        Args:
            filename: The filename to extract date from

        Returns:
            Tuple[Optional[str], Optional[int]]: A tuple containing the date string (YYYY-MM-DD) and increment number
        """
        try:
            filename_str = str(filename)
            match = re.search(r'(\d{4}-\d{2}-\d{2})(?:_(\d+))?', filename_str)
            if match:
                date_str = match.group(1)
                increment = int(match.group(2)) if match.group(2) else 1
                return date_str, increment
            return None, None
        except Exception as e:
            self.logger.error(
                "Error extracting date from filename %s: %s", filename, str(e))
            return None, None

    def get_file_category(self, file_type: FileType) -> FileCategory:
        """Get the category of a file type.

        Args:
            file_type (FileType): Type of file

        Returns:
            FileCategory: Category of the file type
        """
        return self.TYPE_TO_CATEGORY[file_type]

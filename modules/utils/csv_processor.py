"""CSV data processing for the SEO blog generator."""

import csv
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from modules.content_generator.models import KeywordData
from modules.utils.logger import get_logger

logger = get_logger(__name__)


class TopicsCSVProcessor:
    """Process CSV files with keyword data."""

    def __init__(self):
        """Initialize CSV processor."""
        pass

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to match model field names.

        Args:
            df: DataFrame with column names to normalize

        Returns:
            DataFrame with normalized column names
        """
        column_mapping = {
            "Database": "database",
            "Keyword": "keyword",
            "Seed keyword": "seed_keyword",
            "Page": "page",
            "Topic": "topic",
            "Page type": "page_type",
            "Tags": "tags",
            "Volume": "volume",
            "Keyword Difficulty": "keyword_difficulty",
            "CPC (USD)": "cpc_usd",
            "Competitive Density": "competitive_density",
            "Number of Results": "number_of_results",
            "Intent": "intent",
            "SERP Features": "serp_features",
            "Trend": "trend",
            "Click potential": "click_potential",
            "Content references": "content_references",
            "Competitors": "competitors",
        }

        # Normalize column names (lowercase, underscores)
        df.columns = [col.lower().replace(" ", "_") for col in df.columns]

        # Apply direct mappings
        for old_col, new_col in column_mapping.items():
            old_normalized = (
                old_col.lower()
                .replace(" ", "_")
                .replace("(", "_")
                .replace(")", "_")
                .replace("__", "_")
            )
            if old_normalized in df.columns:
                df = df.rename(columns={old_normalized: new_col})

        return df

    def _process_list_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process fields that should be lists or dictionaries.

        Args:
            df: DataFrame with fields to process

        Returns:
            DataFrame with processed fields
        """
        # Fields that should be processed as comma-separated lists
        list_fields = ["tags", "serp_features"]

        for field in list_fields:
            if field in df.columns:
                # Convert comma-separated strings to lists
                df[field] = df[field].apply(
                    lambda x: [item.strip() for item in str(x).split(",")]
                    if pd.notna(x) and x
                    else None
                )

        # Process competitors field as a dictionary with newline-separated items
        if "competitors" in df.columns:
            df["competitors"] = df["competitors"].apply(
                lambda x: self._parse_json_field(x) if pd.notna(x) and x else None
            )
        if "content_references" in df.columns:
            df["content_references"] = df["content_references"].apply(
                lambda x: self._parse_json_field(x) if pd.notna(x) and x else None
            )

        return df

    def _parse_json_field(self, value: str) -> dict:
        """Parse the competitors field which contains newline-separated dictionary entries.

        Args:
            value: String containing competitor data

        Returns:
            Dictionary with domain as key and URL as value
        """
        if not value:
            return {}

        result = {}
        lines = value.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove extra quotes and split by colon
            line = line.strip('"')
            if ":" not in line:
                continue

            parts = line.split(":", 1)
            if len(parts) != 2:
                continue

            domain, url = parts
            # Clean up the domain and url
            domain = domain.strip('"')
            url = url.strip('"')

            result[domain] = url

        return result

    def _process_numeric_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process numeric fields.

        Args:
            df: DataFrame with fields to process

        Returns:
            DataFrame with processed numeric fields
        """
        numeric_fields = {
            "volume": "int",
            "keyword_difficulty": "float",
            "cpc_usd": "float",
            "competitive_density": "float",
            "number_of_results": "int",
        }

        for field, dtype in numeric_fields.items():
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors="coerce")
                if dtype == "int":
                    df[field] = df[field].fillna(0).astype(int)

        return df

    def _process_string_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process string fields, converting NaN values to None.

        Args:
            df: DataFrame with fields to process

        Returns:
            DataFrame with processed string fields
        """
        string_fields = [
            "database",
            "keyword",
            "seed_keyword",
            "page",
            "topic",
            "page_type",
            "intent",
            "trend",
            "click_potential",
            "content_references",
        ]

        for field in string_fields:
            if field in df.columns:
                df[field] = df[field].apply(lambda x: None if pd.isna(x) else x)

        return df

    def read_csv(self, input_path: Union[str, Path]) -> Dict[str, List[KeywordData]]:
        """Read and process the CSV file.

        Returns:
            List of KeywordData objects
        """
        self.input_path = Path(input_path)
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")

        logger.info(f"Reading CSV file: {self.input_path}")

        try:
            # Read CSV into DataFrame
            df = pd.read_csv(self.input_path)

            # Normalize column names
            df = self._normalize_column_names(df)

            # Process fields
            df = self._process_list_fields(df)
            df = self._process_numeric_fields(df)
            df = self._process_string_fields(df)

            df["importance_in_cluster"] = df.apply(
                lambda row: row["volume"] / df[df["page"] == row["page"]]["volume"].sum()
                if not pd.isna(row["volume"]) and df[df["page"] == row["page"]]["volume"].sum() > 0
                else 0,
                axis=1,
            )

            # Convert to KeywordData objects
            keyword_data_dict = {}
            for _, row in df.iterrows():
                try:
                    data_dict = row.to_dict()
                    # Convert any remaining NaN values to None
                    keyword_data = KeywordData(**data_dict)
                    if keyword_data.page not in keyword_data_dict:
                        keyword_data_dict[keyword_data.page] = []
                    keyword_data_dict[keyword_data.page].append(keyword_data)
                except Exception as e:
                    logger.error(f"Error processing row: {e}")
                    logger.debug(f"Row data: {row.to_dict()}")

            logger.info(f"Processed {len(keyword_data_dict)} keyword entries")
            return keyword_data_dict

        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            raise

    @staticmethod
    def write_csv(
        data: List[Dict], output_path: Union[str, Path], fieldnames: Optional[List[str]] = None
    ) -> None:
        """Write data to a CSV file.

        Args:
            data: List of dictionaries to write
            output_path: Path to the output CSV file
            fieldnames: Optional list of field names to use
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure fieldnames is not None for the DictWriter
        field_names = fieldnames or (list(data[0].keys()) if data else [])

        logger.info(f"Writing CSV file: {output_path}")

        try:
            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=field_names)
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"Successfully wrote {len(data)} rows to {output_path}")

        except Exception as e:
            logger.error(f"Error writing CSV: {e}")
            raise

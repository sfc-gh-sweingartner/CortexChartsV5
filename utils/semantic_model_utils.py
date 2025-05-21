"""
Semantic Model Parser Utility
============================
This module provides functionality to parse Snowflake semantic model YAML files
and extract column metadata for use in the Cortex Analyst UI.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import yaml
from enum import Enum

class ColumnType(Enum):
    """Enumeration of possible column types in the semantic model."""
    DIMENSION = "dimension"
    FACT = "fact"
    TIME_DIMENSION = "time_dimension"

@dataclass
class Column:
    """Represents a column in the semantic model."""
    name: str
    description: Optional[str]
    data_type: str
    column_type: ColumnType
    expr: str

@dataclass
class Table:
    """Represents a table in the semantic model."""
    name: str
    description: Optional[str]
    columns: List[Column]

class SemanticModelParser:
    """Parser for Snowflake semantic model YAML files."""
    
    def __init__(self, yaml_content: str):
        """Initialize parser with YAML content.
        
        Args:
            yaml_content: String containing the YAML file content
        """
        self.yaml_content = yaml_content
        self.tables: List[Table] = []

    def parse(self) -> List[Table]:
        """Parse the YAML content and return list of tables with their columns.
        
        Returns:
            List of Table objects containing column metadata
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            data = yaml.safe_load(self.yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {str(e)}")

        if not isinstance(data, dict):
            raise ValueError("Invalid semantic model: root must be a dictionary")

        if "tables" not in data:
            raise ValueError("Invalid semantic model: 'tables' section is required")

        for table_data in data["tables"]:
            self._validate_table_data(table_data)
            table = self._parse_table(table_data)
            self.tables.append(table)

        return self.tables

    def _validate_table_data(self, table_data: Dict) -> None:
        """Validate table data has required fields.
        
        Args:
            table_data: Dictionary containing table definition
            
        Raises:
            ValueError: If required fields are missing
        """
        if not isinstance(table_data, dict):
            raise ValueError("Table definition must be a dictionary")
        
        if "name" not in table_data:
            raise ValueError("Table definition missing required 'name' field")

    def _parse_table(self, table_data: Dict) -> Table:
        """Parse table data into Table object.
        
        Args:
            table_data: Dictionary containing table definition
            
        Returns:
            Table object with parsed columns
        """
        columns = []
        
        # Parse dimensions
        if "dimensions" in table_data:
            for dim in table_data["dimensions"]:
                self._validate_column_data(dim, "dimension")
                columns.append(self._create_column(dim, ColumnType.DIMENSION))

        # Parse facts
        if "facts" in table_data:
            for fact in table_data["facts"]:
                self._validate_column_data(fact, "fact")
                columns.append(self._create_column(fact, ColumnType.FACT))

        # Parse time dimensions
        if "time_dimensions" in table_data:
            for time_dim in table_data["time_dimensions"]:
                self._validate_column_data(time_dim, "time_dimension")
                columns.append(self._create_column(time_dim, ColumnType.TIME_DIMENSION))

        # Sort columns alphabetically by name
        columns.sort(key=lambda x: x.name)

        return Table(
            name=table_data["name"],
            description=table_data.get("description"),
            columns=columns
        )

    def _validate_column_data(self, column_data: Dict, column_type: str) -> None:
        """Validate column data has required fields.
        
        Args:
            column_data: Dictionary containing column definition
            column_type: Type of column being validated
            
        Raises:
            ValueError: If required fields are missing
        """
        if not isinstance(column_data, dict):
            raise ValueError(f"{column_type} definition must be a dictionary")

        required_fields = ["name", "expr", "data_type"]
        for field in required_fields:
            if field not in column_data:
                raise ValueError(f"{column_type} definition missing required '{field}' field")

    def _create_column(self, column_data: Dict, column_type: ColumnType) -> Column:
        """Create Column object from column definition.
        
        Args:
            column_data: Dictionary containing column definition
            column_type: Type of column (dimension/fact/time_dimension)
            
        Returns:
            Column object with parsed metadata
        """
        return Column(
            name=column_data["name"],
            description=column_data.get("description"),
            data_type=column_data["data_type"],
            column_type=column_type,
            expr=column_data["expr"]
        ) 
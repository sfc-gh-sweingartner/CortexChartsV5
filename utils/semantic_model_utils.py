"""
Semantic Model Parser Utility
============================
This module provides functionality to parse Snowflake semantic model YAML files
and extract column metadata for use in the Cortex Analyst UI.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
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
    synonyms: List[str] = field(default_factory=list)
    sample_values: List[Any] = field(default_factory=list)

@dataclass
class Relationship:
    """Represents a relationship between tables in the semantic model."""
    name: str
    from_table: str
    to_table: str
    from_column: str
    to_column: str
    join_type: str = "inner"

@dataclass
class Table:
    """Represents a table in the semantic model."""
    name: str
    description: Optional[str]
    columns: List[Column]
    base_table: Optional[Dict[str, str]] = None
    relationships: List[Relationship] = field(default_factory=list)

class SemanticModelParser:
    """Parser for Snowflake semantic model YAML files."""
    
    def __init__(self, yaml_content: str):
        """Initialize parser with YAML content.
        
        Args:
            yaml_content: String containing the YAML file content
        """
        self.yaml_content = yaml_content
        self.tables: List[Table] = []
        self.errors: List[str] = []

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
            error_msg = f"Invalid YAML format: {str(e)}"
            self.errors.append(error_msg)
            raise ValueError(error_msg)

        if not isinstance(data, dict):
            error_msg = "Invalid semantic model: root must be a dictionary"
            self.errors.append(error_msg)
            raise ValueError(error_msg)

        # If data starts with a document marker (---), the actual content might be in a nested structure
        if "tables" not in data:
            # Try to find tables in any of the nested dictionaries
            found_tables = False
            for key, value in data.items():
                if isinstance(value, dict) and "tables" in value:
                    data = value
                    found_tables = True
                    break
            
            if not found_tables:
                # Print first 100 chars of yaml_content to debug
                preview = self.yaml_content[:500] if isinstance(self.yaml_content, str) else str(self.yaml_content)[:500]
                error_msg = f"Invalid semantic model: 'tables' section is required. YAML preview: {preview}..."
                self.errors.append(error_msg)
                raise ValueError(error_msg)

        # Parse relationships at model level if they exist
        model_relationships = []
        if "relationships" in data:
            try:
                model_relationships = self._parse_relationships(data["relationships"])
            except Exception as e:
                self.errors.append(f"Error parsing model-level relationships: {str(e)}")

        # Parse tables
        for table_data in data["tables"]:
            try:
                self._validate_table_data(table_data)
                table = self._parse_table(table_data)
                
                # Add model-level relationships that apply to this table
                for rel in model_relationships:
                    if rel.from_table == table.name:
                        table.relationships.append(rel)
                
                self.tables.append(table)
            except Exception as e:
                self.errors.append(f"Error parsing table '{table_data.get('name', 'unknown')}': {str(e)}")

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
        
        # Parse base table info if available
        base_table = table_data.get("base_table")
        
        # Parse dimensions
        if "dimensions" in table_data:
            for dim in table_data["dimensions"]:
                self._validate_column_data(dim, "dimension")
                columns.append(self._create_column(dim, ColumnType.DIMENSION))

        # Parse facts (support both 'facts' and 'measures' keys for backward compatibility)
        if "facts" in table_data:
            for fact in table_data["facts"]:
                self._validate_column_data(fact, "fact")
                columns.append(self._create_column(fact, ColumnType.FACT))
                
        # Also check for 'measures' key (backward compatibility)
        if "measures" in table_data:
            for measure in table_data["measures"]:
                self._validate_column_data(measure, "measure")
                columns.append(self._create_column(measure, ColumnType.FACT))

        # Parse time dimensions
        if "time_dimensions" in table_data:
            for time_dim in table_data["time_dimensions"]:
                self._validate_column_data(time_dim, "time_dimension")
                columns.append(self._create_column(time_dim, ColumnType.TIME_DIMENSION))

        # Sort columns alphabetically by name
        columns.sort(key=lambda x: x.name)
        
        # Parse relationships for this table
        relationships = []
        if "relationships" in table_data:
            try:
                relationships = self._parse_relationships(table_data["relationships"], from_table=table_data["name"])
            except Exception as e:
                self.errors.append(f"Error parsing relationships for table '{table_data['name']}': {str(e)}")

        return Table(
            name=table_data["name"],
            description=table_data.get("description"),
            columns=columns,
            base_table=base_table,
            relationships=relationships
        )

    def _parse_relationships(self, relationships_data: List[Dict], from_table: Optional[str] = None) -> List[Relationship]:
        """Parse relationship data into Relationship objects.
        
        Args:
            relationships_data: List of dictionaries containing relationship definitions
            from_table: Optional name of the table these relationships are defined on
            
        Returns:
            List of Relationship objects
        """
        relationships = []
        
        for rel in relationships_data:
            if not isinstance(rel, dict):
                continue
                
            # Validate required fields
            required_fields = ["name", "to_table", "to_column"]
            if all(field in rel for field in required_fields):
                # For table-level relationships, from_table is already known
                # For model-level relationships, from_table and from_column must be specified
                if from_table is None and ("from_table" not in rel or "from_column" not in rel):
                    continue
                
                relationships.append(Relationship(
                    name=rel["name"],
                    from_table=from_table or rel["from_table"],
                    to_table=rel["to_table"],
                    from_column=rel.get("from_column", ""),
                    to_column=rel["to_column"],
                    join_type=rel.get("join_type", "inner")
                ))
                
        return relationships

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
        # Make sure to handle missing or invalid synonyms and sample_values
        synonyms = []
        sample_values = []
        
        # Get synonyms with error handling
        if "synonyms" in column_data:
            if isinstance(column_data["synonyms"], list):
                synonyms = column_data["synonyms"]
            else:
                self.errors.append(f"Invalid synonyms format for column '{column_data.get('name', 'unknown')}': expected list")
        
        # Get sample_values with error handling
        if "sample_values" in column_data:
            if isinstance(column_data["sample_values"], list):
                sample_values = column_data["sample_values"]
            else:
                self.errors.append(f"Invalid sample_values format for column '{column_data.get('name', 'unknown')}': expected list")
        
        return Column(
            name=column_data["name"],
            description=column_data.get("description"),
            data_type=column_data["data_type"],
            column_type=column_type,
            expr=column_data["expr"],
            synonyms=synonyms,
            sample_values=sample_values
        )

    def get_columns_by_type(self, column_type: ColumnType) -> Dict[str, List[Column]]:
        """Get all columns of a specific type, grouped by table.
        
        Args:
            column_type: Type of columns to retrieve
            
        Returns:
            Dictionary mapping table names to lists of columns
        """
        result: Dict[str, List[Column]] = {}
        
        for table in self.tables:
            table_columns = [col for col in table.columns if col.column_type == column_type]
            if table_columns:
                result[table.name] = table_columns
                
        return result
    
    def get_errors(self) -> List[str]:
        """Get any errors encountered during parsing.
        
        Returns:
            List of error messages
        """
        return self.errors 
"""
Semantic Model Parser Utility
============================
This module provides functionality to parse Snowflake semantic model YAML files
and extract column metadata for use in the Cortex Analyst UI.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple
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
        """Initialize the parser with YAML content.
        
        Args:
            yaml_content: String containing YAML content
        """
        self.yaml_content = yaml_content
        self.tables: List[Table] = []
        self.errors: List[str] = []
        self.debug_messages: List[str] = []
        
    def parse(self) -> Tuple[List[Table], List[str]]:
        """Parse the YAML content and return list of tables with their columns.
        
        Returns:
            Tuple containing:
              - List of Table objects containing column metadata
              - List of debug messages
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Add debug information about the content type and length
        content_type = type(self.yaml_content).__name__
        content_length = len(self.yaml_content) if isinstance(self.yaml_content, (str, bytes)) else 0
        self.debug_messages.append(f"YAML content type={content_type}, length={content_length}")
        
        if content_length > 0 and isinstance(self.yaml_content, str):
            preview = self.yaml_content[:200].replace('\n', '\\n')
            self.debug_messages.append(f"YAML content preview: {preview}...")
        
        try:
            data = yaml.safe_load(self.yaml_content)
            # Debug the loaded data
            data_type = type(data).__name__
            self.debug_messages.append(f"Loaded data type={data_type}")
            
            if data is None:
                self.debug_messages.append("YAML parsed as None - file may be empty or have only comments")
            elif isinstance(data, str):
                preview = data[:100].replace('\n', '\\n')
                self.debug_messages.append(f"YAML parsed as string: {preview}...")
            elif isinstance(data, list):
                self.debug_messages.append(f"YAML parsed as list with {len(data)} items")
                if len(data) > 0:
                    self.debug_messages.append(f"First item type: {type(data[0]).__name__}")
        except yaml.YAMLError as e:
            error_msg = f"Invalid YAML format: {str(e)}"
            self.errors.append(error_msg)
            self.debug_messages.append(f"YAML parsing error: {error_msg}")
            raise ValueError(error_msg)

        if data is None or not isinstance(data, dict):
            # Try to recover - if it's a string, try re-parsing after some cleanup
            if isinstance(self.yaml_content, str):
                self.debug_messages.append("Attempting recovery - cleaning up content and re-parsing")
                clean_content = self.yaml_content.strip()
                
                # Try to handle UTF-8 BOM if present
                if clean_content.startswith('\ufeff'):
                    clean_content = clean_content[1:]
                    self.debug_messages.append("Removed UTF-8 BOM marker")
                
                try:
                    data = yaml.safe_load(clean_content)
                    self.debug_messages.append(f"After cleanup, loaded data type={type(data).__name__}")
                    
                    if not isinstance(data, dict):
                        error_msg = f"Invalid semantic model: root must be a dictionary, got {type(data).__name__}"
                        self.errors.append(error_msg)
                        self.debug_messages.append(f"Recovery failed: {error_msg}")
                        raise ValueError(error_msg)
                except Exception as e:
                    self.debug_messages.append(f"Recovery attempt failed: {str(e)}")
            
            error_msg = "Invalid semantic model: root must be a dictionary"
            self.errors.append(error_msg)
            raise ValueError(error_msg)

        # If data starts with a document marker (---), the actual content might be in a nested structure
        if "tables" not in data:
            # Try to find tables in any of the nested dictionaries
            found_tables = False
            self.debug_messages.append("'tables' key not found in root, searching in nested dictionaries")
            for key, value in data.items():
                self.debug_messages.append(f"Checking key '{key}', type={type(value).__name__}")
                if isinstance(value, dict) and "tables" in value:
                    data = value
                    found_tables = True
                    self.debug_messages.append(f"Found 'tables' key in '{key}' dictionary")
                    break
            
            if not found_tables:
                # Print first 100 chars of yaml_content to debug
                preview = self.yaml_content[:500] if isinstance(self.yaml_content, str) else str(self.yaml_content)[:500]
                preview = preview.replace('\n', '\\n')
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

        return self.tables, self.debug_messages

    def _validate_table_data(self, table_data: Dict) -> None:
        """Validate table data has required fields.
        
        Args:
            table_data: Dictionary containing table definition
            
        Raises:
            ValueError: If required fields are missing
        """
        # Check for required fields
        if "name" not in table_data:
            raise ValueError("Table is missing required 'name' field")
            
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

        # Parse facts (support both 'facts' and 'measures' keys)
        facts_key = None
        if "facts" in table_data:
            facts_key = "facts"
        elif "measures" in table_data:
            facts_key = "measures"
            self.debug_messages.append(f"Using 'measures' key instead of 'facts' for table {table_data['name']}")
            
        if facts_key:
            for fact in table_data[facts_key]:
                self._validate_column_data(fact, "fact")
                columns.append(self._create_column(fact, ColumnType.FACT))
                
        # Parse time dimensions
        if "time_dimensions" in table_data:
            for time_dim in table_data["time_dimensions"]:
                self._validate_column_data(time_dim, "time_dimension")
                columns.append(self._create_column(time_dim, ColumnType.TIME_DIMENSION))
                
        # Parse table-level relationships
        relationships = []
        if "relationships" in table_data:
            from_table = table_data["name"]
            relationships = self._parse_relationships(table_data["relationships"], from_table)
                
        return Table(
            name=table_data["name"],
            description=table_data.get("description"),
            columns=columns,
            base_table=base_table,
            relationships=relationships
        )
        
    def _parse_relationships(self, relationships_data: List[Dict], from_table: Optional[str] = None) -> List[Relationship]:
        """Parse relationships from YAML data.
        
        Args:
            relationships_data: List of relationship definitions
            from_table: Optional source table name to use if not specified in relationship
            
        Returns:
            List of Relationship objects
        """
        relationships = []
        for rel_data in relationships_data:
            # Handle different relationship formats
            if "left_table" in rel_data and "right_table" in rel_data:
                # New format with relationship_columns
                from_table_name = rel_data["left_table"]
                to_table_name = rel_data["right_table"]
                
                # Get the first column pair
                if "relationship_columns" in rel_data:
                    col_pair = rel_data["relationship_columns"][0]
                    from_col = col_pair.get("left_column", "")
                    to_col = col_pair.get("right_column", "")
                else:
                    # Fallback to direct columns if relationship_columns is missing
                    from_col = "unknown"
                    to_col = "unknown"
                    
                join_type = rel_data.get("join_type", "inner")
                
            elif "to_table" in rel_data and "column" in rel_data and "to_column" in rel_data:
                # Old format with direct column references
                from_table_name = from_table or "unknown"
                to_table_name = rel_data["to_table"]
                from_col = rel_data["column"]
                to_col = rel_data["to_column"]
                join_type = rel_data.get("join_type", "inner")
            else:
                # Skip invalid relationship
                continue
                
            relationships.append(Relationship(
                name=rel_data.get("name", f"{from_table_name}_to_{to_table_name}"),
                from_table=from_table_name,
                to_table=to_table_name,
                from_column=from_col,
                to_column=to_col,
                join_type=join_type
            ))
            
        return relationships
    
    def _validate_column_data(self, column_data: Dict, column_type: str) -> None:
        """Validate column data has required fields.
        
        Args:
            column_data: Dictionary containing column definition
            column_type: Type of column (dimension, fact, time_dimension)
            
        Raises:
            ValueError: If required fields are missing
        """
        # Check for required fields
        required_fields = ["name", "expr", "data_type"]
        for field in required_fields:
            if field not in column_data:
                raise ValueError(f"{column_type.capitalize()} is missing required '{field}' field")
    
    def _create_column(self, column_data: Dict, column_type: ColumnType) -> Column:
        """Create a Column object from column data.
        
        Args:
            column_data: Dictionary containing column definition
            column_type: Type of column (DIMENSION, FACT, TIME_DIMENSION)
            
        Returns:
            Column object with parsed metadata
        """
        # Extract basic info
        name = column_data["name"]
        expr = column_data["expr"]
        data_type = column_data["data_type"]
        description = column_data.get("description")
        
        # Handle synonyms
        synonyms = []
        if "synonyms" in column_data and column_data["synonyms"]:
            # Remove any empty or whitespace-only synonyms
            synonyms = [s for s in column_data["synonyms"] if s and s.strip() and s.strip() != "  "]
            
        # Handle sample values
        sample_values = []
        if "sample_values" in column_data and column_data["sample_values"]:
            sample_values = column_data["sample_values"]
            
        return Column(
            name=name,
            description=description,
            data_type=data_type,
            column_type=column_type,
            expr=expr,
            synonyms=synonyms,
            sample_values=sample_values
        )
        
    def get_columns_by_type(self, column_type: ColumnType) -> Dict[str, List[Column]]:
        """Get all columns of a specific type grouped by table.
        
        Args:
            column_type: Type of columns to retrieve
            
        Returns:
            Dictionary mapping table names to lists of columns
        """
        result = {}
        for table in self.tables:
            columns = [col for col in table.columns if col.column_type == column_type]
            if columns:
                result[table.name] = columns
        return result
    
    def get_errors(self) -> List[str]:
        """Get list of errors encountered during parsing.
        
        Returns:
            List of error messages
        """
        return self.errors
        
    def get_debug_messages(self) -> List[str]:
        """Get list of debug messages collected during parsing.
        
        Returns:
            List of debug messages
        """
        return self.debug_messages 
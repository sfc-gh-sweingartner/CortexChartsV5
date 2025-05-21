"""
Unit tests for the semantic model parser utility.
"""
import unittest
from utils.semantic_model_utils import (
    SemanticModelParser, ColumnType, Column, Table, Relationship
)

class TestSemanticModelParser(unittest.TestCase):
    """Test cases for the SemanticModelParser class."""
    
    def test_parse_basic_model(self):
        """Test parsing a simple semantic model with one table."""
        yaml_content = """
name: test_model
tables:
  - name: TEST_TABLE
    dimensions:
      - name: DIMENSION1
        expr: DIMENSION1
        data_type: VARCHAR
    facts:
      - name: FACT1
        expr: FACT1
        data_type: NUMBER
    time_dimensions:
      - name: DATE1
        expr: DATE1
        data_type: DATE
"""
        parser = SemanticModelParser(yaml_content)
        tables = parser.parse()
        
        # Assertions
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0].name, "TEST_TABLE")
        self.assertEqual(len(tables[0].columns), 3)
        
        # Check column types
        column_types = {col.name: col.column_type for col in tables[0].columns}
        self.assertEqual(column_types["DIMENSION1"], ColumnType.DIMENSION)
        self.assertEqual(column_types["FACT1"], ColumnType.FACT)
        self.assertEqual(column_types["DATE1"], ColumnType.TIME_DIMENSION)
    
    def test_parse_with_synonyms_and_samples(self):
        """Test parsing columns with synonyms and sample values."""
        yaml_content = """
name: test_model
tables:
  - name: TEST_TABLE
    dimensions:
      - name: DIMENSION1
        expr: DIMENSION1
        data_type: VARCHAR
        synonyms:
          - dim1
          - d1
        sample_values:
          - "Sample 1"
          - "Sample 2"
"""
        parser = SemanticModelParser(yaml_content)
        tables = parser.parse()
        
        # Get the dimension column
        dimension = next((col for col in tables[0].columns if col.name == "DIMENSION1"), None)
        
        # Assertions
        self.assertIsNotNone(dimension)
        self.assertEqual(len(dimension.synonyms), 2)
        self.assertIn("dim1", dimension.synonyms)
        self.assertIn("d1", dimension.synonyms)
        
        self.assertEqual(len(dimension.sample_values), 2)
        self.assertIn("Sample 1", dimension.sample_values)
        self.assertIn("Sample 2", dimension.sample_values)
    
    def test_parse_with_relationships(self):
        """Test parsing tables with relationships."""
        yaml_content = """
name: test_model
tables:
  - name: TABLE1
    dimensions:
      - name: ID
        expr: ID
        data_type: VARCHAR
    relationships:
      - name: to_table2
        to_table: TABLE2
        to_column: TABLE1_ID
  - name: TABLE2
    dimensions:
      - name: TABLE1_ID
        expr: TABLE1_ID
        data_type: VARCHAR
"""
        parser = SemanticModelParser(yaml_content)
        tables = parser.parse()
        
        # Find tables by name
        table1 = next((t for t in tables if t.name == "TABLE1"), None)
        table2 = next((t for t in tables if t.name == "TABLE2"), None)
        
        # Assertions
        self.assertIsNotNone(table1)
        self.assertIsNotNone(table2)
        self.assertEqual(len(table1.relationships), 1)
        
        relationship = table1.relationships[0]
        self.assertEqual(relationship.name, "to_table2")
        self.assertEqual(relationship.from_table, "TABLE1")
        self.assertEqual(relationship.to_table, "TABLE2")
        self.assertEqual(relationship.to_column, "TABLE1_ID")
    
    def test_parse_with_model_level_relationships(self):
        """Test parsing a model with relationships at the model level."""
        yaml_content = """
name: test_model
relationships:
  - name: table1_to_table2
    from_table: TABLE1
    from_column: ID
    to_table: TABLE2
    to_column: TABLE1_ID
    join_type: left
tables:
  - name: TABLE1
    dimensions:
      - name: ID
        expr: ID
        data_type: VARCHAR
  - name: TABLE2
    dimensions:
      - name: TABLE1_ID
        expr: TABLE1_ID
        data_type: VARCHAR
"""
        parser = SemanticModelParser(yaml_content)
        tables = parser.parse()
        
        # Find tables by name
        table1 = next((t for t in tables if t.name == "TABLE1"), None)
        
        # Assertions
        self.assertIsNotNone(table1)
        self.assertEqual(len(table1.relationships), 1)
        
        relationship = table1.relationships[0]
        self.assertEqual(relationship.name, "table1_to_table2")
        self.assertEqual(relationship.from_table, "TABLE1")
        self.assertEqual(relationship.from_column, "ID")
        self.assertEqual(relationship.to_table, "TABLE2")
        self.assertEqual(relationship.to_column, "TABLE1_ID")
        self.assertEqual(relationship.join_type, "left")
    
    def test_get_columns_by_type(self):
        """Test getting columns by type."""
        yaml_content = """
name: test_model
tables:
  - name: TABLE1
    dimensions:
      - name: DIM1
        expr: DIM1
        data_type: VARCHAR
      - name: DIM2
        expr: DIM2
        data_type: VARCHAR
    facts:
      - name: FACT1
        expr: FACT1
        data_type: NUMBER
  - name: TABLE2
    facts:
      - name: FACT2
        expr: FACT2
        data_type: NUMBER
"""
        parser = SemanticModelParser(yaml_content)
        parser.parse()
        
        # Get dimensions
        dimensions = parser.get_columns_by_type(ColumnType.DIMENSION)
        facts = parser.get_columns_by_type(ColumnType.FACT)
        
        # Assertions
        self.assertEqual(len(dimensions), 1)  # One table has dimensions
        self.assertEqual(len(dimensions["TABLE1"]), 2)  # Two dimensions in TABLE1
        
        self.assertEqual(len(facts), 2)  # Two tables have facts
        self.assertEqual(len(facts["TABLE1"]), 1)  # One fact in TABLE1
        self.assertEqual(len(facts["TABLE2"]), 1)  # One fact in TABLE2
    
    def test_invalid_yaml(self):
        """Test handling of invalid YAML syntax."""
        yaml_content = """
name: invalid
tables: [
  {
    name: "Bad YAML
"""
        parser = SemanticModelParser(yaml_content)
        
        # This should raise a ValueError
        with self.assertRaises(ValueError):
            parser.parse()
        
        # Check that errors were recorded
        self.assertTrue(len(parser.get_errors()) > 0)

    def test_missing_tables_section(self):
        """Test handling of missing 'tables' section."""
        yaml_content = """
name: test_model
description: Model without tables
"""
        parser = SemanticModelParser(yaml_content)
        
        # This should raise a ValueError
        with self.assertRaises(ValueError):
            parser.parse()
        
        # Check that errors were recorded
        errors = parser.get_errors()
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any("'tables' section is required" in error for error in errors))

if __name__ == "__main__":
    unittest.main() 
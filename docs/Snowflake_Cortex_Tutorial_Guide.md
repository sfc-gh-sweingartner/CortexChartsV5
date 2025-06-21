# Snowflake Cortex Analyst Tutorial Guide

## Tutorial: Answer Questions About Time-Series Revenue Data with Cortex Analyst

### Introduction

Cortex Analyst transforms natural-language questions about your data into results by generating and executing SQL queries. This tutorial describes how to set up Cortex Analyst to respond to questions about a time-series revenue data set.

### What You Will Learn

- Establish a semantic model for the data set
- Create a Streamlit app that queries Cortex Analyst
- Understand the relationship between semantic models and data analysis
- Implement natural language to SQL query conversion

### Prerequisites

The following prerequisites are required to complete this tutorial:

- **Snowflake Account**: You have a Snowflake account and user with a role that grants the necessary privileges to create:
  - Database
  - Schema
  - Tables
  - Stage
  - Virtual warehouse objects
- **Streamlit Setup**: You have Streamlit set up on your local system
- **Basic Knowledge**: Familiarity with SQL and data analysis concepts

**Reference**: Refer to the "Snowflake in 20 minutes" guide for instructions to meet these requirements.

## Step 1: Setup

### Getting the Sample Data

You will use a sample dataset downloaded from GitHub. Download the following data files to your system:

#### Required Data Files:
1. **`daily_revenue.csv`** - Time-series revenue data
2. **`product.csv`** - Product information and metadata
3. **`region.csv`** - Regional data and classifications

#### Semantic Model File:
- **Semantic model YAML** - Download from GitHub

### Understanding the Semantic Model

The semantic model is a critical component that you should examine before proceeding. The semantic model supplements the SQL schema of each table with additional information that helps Cortex Analyst understand questions about the data.

#### Key Aspects of Semantic Models:
- **Business Context**: Provides business meaning to technical column names
- **Relationships**: Defines how tables relate to each other
- **Metrics Definition**: Specifies how business metrics should be calculated
- **Data Types**: Clarifies the semantic meaning of different data types
- **Descriptions**: Adds human-readable descriptions for columns and tables

**Important Note**: In a non-tutorial setting, you would bring your own data, possibly already in a Snowflake table, and develop your own semantic model.

## Data Structure Overview

### Daily Revenue Data (`daily_revenue.csv`)
This file contains time-series data with:
- **Date Information**: Daily timestamps for revenue tracking
- **Revenue Metrics**: Various revenue measurements and calculations
- **Dimensional Attributes**: Categories and classifications for analysis

### Product Data (`product.csv`)
This file provides product-related information:
- **Product Identifiers**: Unique product codes and names
- **Product Categories**: Hierarchical product classifications
- **Product Attributes**: Descriptive information about products

### Regional Data (`region.csv`)
This file contains geographical information:
- **Region Identifiers**: Unique region codes and names
- **Geographical Hierarchies**: Country, state, city relationships
- **Regional Attributes**: Demographic and market information

## Semantic Model Specification

### YAML Structure
The semantic model is defined in a YAML file that follows Snowflake's Cortex Analyst semantic model specification. This specification includes:

#### Table Definitions
- **Table Names**: Physical table names in Snowflake
- **Table Descriptions**: Business purpose of each table
- **Primary Keys**: Unique identifiers for each table

#### Column Specifications
- **Column Names**: Physical column names
- **Data Types**: Technical data types (string, number, date, etc.)
- **Semantic Types**: Business meaning (dimension, measure, time_dimension)
- **Descriptions**: Human-readable explanations of column purpose

#### Relationships
- **Join Conditions**: How tables connect to each other
- **Cardinality**: One-to-one, one-to-many, many-to-many relationships
- **Join Types**: Inner, left, right, full outer joins

#### Metrics and Calculations
- **Derived Metrics**: Calculated fields based on existing columns
- **Aggregations**: Sum, average, count, and other statistical functions
- **Business Rules**: Specific calculation logic for business metrics

## Implementation Steps

### Step 2: Database Setup (Implied)
While not explicitly detailed in the provided documentation, the tutorial would typically include:

1. **Create Database Objects**:
   - Create a new database for the tutorial
   - Set up appropriate schema
   - Create tables matching the CSV structure

2. **Load Sample Data**:
   - Create stages for data loading
   - Upload CSV files to Snowflake stages
   - Load data into tables using COPY commands

3. **Verify Data Quality**:
   - Check data loading success
   - Validate data types and formats
   - Ensure referential integrity

### Step 3: Semantic Model Configuration
1. **Upload Semantic Model**:
   - Place the YAML file in an accessible location
   - Configure Cortex Analyst to use the semantic model
   - Validate semantic model syntax and structure

2. **Test Semantic Model**:
   - Verify table and column mappings
   - Test relationship definitions
   - Validate metric calculations

### Step 4: Streamlit Application Development
1. **Create Streamlit App**:
   - Set up basic Streamlit application structure
   - Configure Snowflake connection
   - Implement Cortex Analyst API integration

2. **User Interface Design**:
   - Create input fields for natural language queries
   - Design output display for results and visualizations
   - Add error handling and user feedback

3. **Query Processing**:
   - Implement natural language query submission
   - Handle Cortex Analyst API responses
   - Display generated SQL and results

## Best Practices for Tutorial Implementation

### Data Preparation
- **Clean Data**: Ensure sample data is clean and representative
- **Consistent Formats**: Use consistent date formats and data types
- **Complete Relationships**: Ensure all foreign key relationships are valid

### Semantic Model Design
- **Clear Descriptions**: Write clear, business-friendly descriptions
- **Logical Grouping**: Group related columns and tables logically
- **Comprehensive Coverage**: Include all relevant business concepts

### Application Development
- **User Experience**: Design intuitive interfaces for business users
- **Error Handling**: Implement robust error handling and user feedback
- **Performance**: Optimize for reasonable response times

### Testing and Validation
- **Query Testing**: Test with various types of natural language queries
- **Result Validation**: Verify that generated SQL produces correct results
- **Edge Cases**: Test with complex and edge case scenarios

## Expected Outcomes

### Functional Capabilities
After completing the tutorial, you should have:
- **Working Streamlit Application**: A functional app that accepts natural language queries
- **Cortex Analyst Integration**: Successful integration with Cortex Analyst API
- **Query Processing**: Ability to convert natural language to SQL and execute queries
- **Result Display**: Clear presentation of query results and generated SQL

### Learning Achievements
- **Semantic Model Understanding**: Deep understanding of how semantic models work
- **API Integration**: Experience with Cortex Analyst API integration
- **Natural Language Processing**: Understanding of text-to-SQL conversion
- **Business Intelligence**: Knowledge of self-service analytics implementation

## Common Use Cases Demonstrated

### Time-Series Analysis
- "What was the revenue trend over the last quarter?"
- "Show me monthly revenue by product category"
- "Which regions had the highest growth rate?"

### Comparative Analysis
- "Compare product performance across different regions"
- "What are the top-performing products by revenue?"
- "How does this year's performance compare to last year?"

### Drill-Down Queries
- "Show me detailed revenue breakdown for Product X"
- "What drove the revenue spike in March?"
- "Which specific products contributed most to regional performance?"

## Troubleshooting Common Issues

### Data Loading Problems
- **File Format Issues**: Ensure CSV files have correct delimiters and encoding
- **Data Type Mismatches**: Verify data types match semantic model specifications
- **Missing Values**: Handle null values appropriately in the data

### Semantic Model Issues
- **YAML Syntax Errors**: Validate YAML syntax and structure
- **Table/Column Mismatches**: Ensure semantic model matches actual database schema
- **Relationship Errors**: Verify join conditions and table relationships

### API Integration Problems
- **Authentication Issues**: Ensure proper Snowflake authentication setup
- **Permission Problems**: Verify user has necessary privileges for Cortex Analyst
- **Network Connectivity**: Check network connectivity to Snowflake

### Query Processing Issues
- **Ambiguous Queries**: Provide clearer, more specific natural language queries
- **Complex Requests**: Break down complex requests into simpler components
- **Performance Problems**: Optimize queries and consider data volume impacts

## Extensions and Next Steps

### Advanced Features
- **Custom Visualizations**: Add charts and graphs to result displays
- **Query History**: Implement query history and favorites functionality
- **Export Capabilities**: Add data export features for results
- **Dashboard Integration**: Connect to business intelligence dashboards

### Production Considerations
- **Security**: Implement proper authentication and authorization
- **Scalability**: Design for multiple concurrent users
- **Monitoring**: Add logging and monitoring capabilities
- **Governance**: Implement data governance and compliance features

### Integration Opportunities
- **Business Applications**: Integrate with existing business applications
- **Slack/Teams**: Add chatbot capabilities for collaboration platforms
- **Mobile Applications**: Develop mobile interfaces for analytics
- **Automated Reporting**: Create scheduled report generation capabilities

This tutorial provides a comprehensive foundation for understanding and implementing Cortex Analyst in real-world scenarios, preparing you for more advanced use cases and production deployments. 
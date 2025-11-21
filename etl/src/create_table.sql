-- SQL script to create the table for the provided CSV structure in PostgreSQL

CREATE TABLE etl.enterprise_survey (
    Year INT NOT NULL,
    Industry_aggregation_NZSIOC VARCHAR(50),
    Industry_code_NZSIOC VARCHAR(10),
    Industry_name_NZSIOC VARCHAR(255),
    Units VARCHAR(50),
    Variable_code VARCHAR(10),
    Variable_name VARCHAR(100),
    Variable_category VARCHAR(100),
    Value NUMERIC,
    Industry_code_ANZSIC06 VARCHAR(255)
);

-- Add any additional constraints or indexes as needed
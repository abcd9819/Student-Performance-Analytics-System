# Student Analytics System

A Python-based command-line application for managing and analyzin
student information and academic performance. The project loads student
details and grades from CSV files, combines the records, and provides
tools for viewing student marksheets, analyzing data, visualizing
results, and generating reports.

## Features

-   **Student data loading:** Reads student details and grade records
    from CSV files.
-   **Data validation:** Checks required columns, cleans column names,
    normalizes student IDs, and detects duplicate student IDs in the
    personal-data file.
-   **Student marksheet:** Looks up a student by ID and displays their
    academic information and marks.
-   **Data analysis:** Uses Pandas to process and analyze student
    records.
-   **Rich terminal output:** Uses Rich to display readable, formatted
    command-line output.
-   **Charts and visualization:** Uses Matplotlib to visualize data;
    `mplcursors` can add interactive chart details.
-   **PDF reports:** Uses ReportLab to generate PDF marksheets or
    reports.
-   **Database support:** Includes SQLite configuration for storing or
    working with student records.

## Technology Stack

  Technology   Purpose
  ------------ ----------------------------------
  Python       Main programming language
  Pandas       CSV processing and data analysis
  Rich         Formatted terminal interface
  Matplotlib   Data visualization
  mplcursors   Interactive chart annotations
  SQLite       Local database support
  ReportLab    PDF report generation

## Project Structure

The project is expected to contain files similar to the following:

``` text
student-analytics-system/
├── main.py
├── functions.py
├── dummy_student_data.csv
├── dummy_student_grades.csv
├── student_database.db       # Created or used by the application
└── reports/                  # Generated reports, if enabled
```

The exact contents may differ depending on your local project setup.

## Requirements

-   Python 3.10 or a compatible newer Python version
-   The CSV input files used by the application
-   The Python packages imported by the project

## Installation

### 1. Open the project directory

Open a terminal in the folder containing `main.py` and `functions.py`.

### 2. Create a virtual environment (recommended)

**Windows:**

``` bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

Install the packages used by the project:

``` bash
python -m pip install pandas rich matplotlib mplcursors reportlab
```

If the code imports additional third-party packages, install those
packages as well.

## Input Data

The application uses two CSV files.

### `dummy_student_data.csv`

Contains personal and enrollment information. Depending on the dataset,
columns may include:

-   `StudentID`
-   `FirstName`
-   `LastName`
-   `Gender`
-   `DateOfBirth`
-   `Grade`
-   `Section`
-   `Stream`
-   `AttendancePercent`
-   `EnrollmentDate`
-   `Status`
-   `Email`
-   `PhoneNumber`
-   `City`
-   `State`
-   `BloodGroup`
-   `GuardianName`
-   `GuardianPhone`

### `dummy_student_grades.csv`

Contains student grade or marks records. The exact columns depend on the
dataset and may include student IDs, exam terms, subject marks, totals,
percentages, grades, or GPA.

**Important:** Column names in the CSV files must match the names
expected by the Python code. The `StudentID` column is used to connect
the personal records and grade records. Each student ID should be unique
in the personal-data file. A student may have multiple grade records for
different exams or terms.

## Run the Application

From the project directory, run:

``` bash
python main.py
```

Follow the numbered menu displayed in the terminal. For example, if the
marksheet feature is assigned option `4`, select that option and enter a
student ID such as:

``` text
STU0280
```

Use an ID that actually exists in your CSV files.

## Data Processing Overview

1.  Read the personal and grade CSV files with Pandas.
2.  Trim spaces from column names and student IDs.
3.  Standardize student IDs to uppercase.
4.  Validate required columns and detect duplicate personal records.
5.  Rename the personal-data `Grade` column to `ClassGrade` when
    applicable.
6.  Remove overlapping personal-detail columns from the grades data
    before merging.
7.  Merge the two datasets using `StudentID`.
8.  Display or analyze the combined records.

The merge should be performed only after column names have been
standardized. This helps prevent duplicate columns such as
`ClassGrade_x` and `ClassGrade_y`, which can cause a `KeyError` when the
marksheet expects `ClassGrade`.

## Troubleshooting

### `KeyError: 'ClassGrade'`

**Cause:** The merged DataFrame does not contain a column named
`ClassGrade`. This can happen when the two CSV files have overlapping
columns or when the `Grade` column is renamed after the merge.

**What to check:**

1.  Confirm that the personal CSV contains `Grade` or `ClassGrade`.
2.  Rename `Grade` to `ClassGrade` before merging.
3.  Check for columns named `ClassGrade_x` or `ClassGrade_y`.
4.  Confirm that the application is loading the expected CSV files.

### CSV file not found

-   Confirm that both CSV files are in the expected project directory.
-   Check the filenames and capitalization.
-   If the files are stored elsewhere, update the paths in the code.

### Student not found

-   Confirm that the student ID exists in the personal-data CSV.
-   Check for extra spaces or spelling differences.
-   Ensure the ID is present in the grades CSV if a marksheet requires
    grade records.

### Missing marksheet fields

The marksheet may expect columns such as `ExamTerm`, subject names,
`Total`, `MaxPossible`, `Percentage`, `OverallGrade`, or `GPA`. Check
the exact column names in `dummy_student_grades.csv` and update the code
or dataset consistently.

## Suggested Improvements

-   Add a `requirements.txt` file to make dependency installation
    easier.
-   Add automated tests for CSV loading, merging, and marksheet
    generation.
-   Validate marks and attendance ranges.
-   Add clearer error messages for missing columns and invalid student
    IDs.
-   Keep generated reports in the `reports/` directory.
-   Add database initialization and backup procedures if SQLite is used
    for persistent storage.
-   Avoid committing real student personal information, phone numbers,
    email addresses, or other sensitive data to a public repository.

## Privacy and Security

Use fictional or anonymized student data when demonstrating or
publishing the project. Do not upload real student records or sensitive
personal information to a public Git repository.

## License

No license has been specified. Add a license file before distributing
the project if you want to define how others may use, modify, or
redistribute it.

## Author

**Project:** Student Analytics System\
**Language:** Python\
**Type:** Command-line data analysis application

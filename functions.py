
import sqlite3
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import mplcursors

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, IntPrompt
from rich import box

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table as PDFTable,
    TableStyle,
)

# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

PERSONAL_FILE = BASE_DIR / "dummy_student_data.csv"
GRADES_FILE = BASE_DIR / "dummy_student_grades.csv"
DATABASE_FILE = BASE_DIR / "student_database.db"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(exist_ok=True)

console = Console()

SUBJECTS = [
    "English",
    "Mathematics",
    "Science",
    "Social Studies",
    "Computer Science",
    "Physics",
    "Chemistry",
    "Biology",
    "Accountancy",
    "Business Studies",
    "Economics",
    "History",
    "Political Science",
    "Psychology",
]


# =========================================================
# TERMINAL UI
# =========================================================

def show_title():
    console.clear()

    title = Text()
    title.append("STUDENT ", style="bold bright_cyan")
    title.append("ANALYTICAL SYSTEM", style="bold bright_magenta")

    console.print(
        Panel(
            title,
            subtitle="[dim]Academic Performance & Student Insights[/dim]",
            border_style="bright_cyan",
            box=box.DOUBLE,
            padding=(1, 2),
        )
    )


def show_message(message, style="green"):
    console.print(f"\n[{style}]{message}[/{style}]")


def pause():
    console.input("\n[dim]Press Enter to continue...[/dim]")


def show_menu():
    table = Table(
        title="MAIN MENU",
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold bright_cyan",
        expand=True,
    )

    table.add_column("Option", style="bold yellow", justify="center", width=10)
    table.add_column("Feature", style="white")

    options = [
        ("1", "View all student records"),
        ("2", "Search student"),
        ("3", "View student profile"),
        ("4", "View academic marksheet"),
        ("5", "Filter student records"),
        ("6", "Academic analysis dashboard"),
        ("7", "Interactive graphs"),
        ("8", "Export records to CSV"),
        ("9", "Export records to Excel"),
        ("10", "Generate PDF marksheet"),
        ("11", "Reload CSV files"),
        ("0", "Exit application"),
    ]

    for option, feature in options:
        table.add_row(option, feature)

    console.print(table)


# =========================================================
# DATA LOADING AND MERGING
# =========================================================


def load_data():
    """Load student personal details and grades, then merge them safely."""
    try:
        # Check that both CSV files exist.
        if not PERSONAL_FILE.exists():
            console.print(
                f"[red]Error: Personal data file not found: {PERSONAL_FILE}[/red]"
            )
            return None

        if not GRADES_FILE.exists():
            console.print(
                f"[red]Error: Grades file not found: {GRADES_FILE}[/red]"
            )
            return None

        # Read CSV files.
        personal = pd.read_csv(PERSONAL_FILE)
        grades = pd.read_csv(GRADES_FILE)

        # Remove unnecessary spaces from column names.
        personal.columns = personal.columns.str.strip()
        grades.columns = grades.columns.str.strip()

        # Standardize StudentID.
        for df in (personal, grades):
            if "StudentID" not in df.columns:
                console.print(
                    "[red]Error: StudentID column is missing from a CSV file.[/red]"
                )
                return None

            df["StudentID"] = (
                df["StudentID"].astype("string").str.strip().str.upper()
            )

            df.dropna(subset=["StudentID"], inplace=True)

            df.drop(
                df[df["StudentID"].eq("")].index,
                inplace=True
            )

        # Prevent duplicate student IDs in the personal data.
        if personal["StudentID"].duplicated().any():
            duplicates = personal.loc[
                personal["StudentID"].duplicated(keep=False),
                "StudentID"
            ].unique()

            console.print(
                f"[red]Error: Duplicate StudentID values in personal data: "
                f"{', '.join(duplicates)}[/red]"
            )
            return None

        # Rename Grade consistently BEFORE merging.
        if "Grade" in personal.columns:
            personal.rename(
                columns={"Grade": "ClassGrade"},
                inplace=True
            )

        if "Grade" in grades.columns:
            grades.rename(
                columns={"Grade": "ClassGrade"},
                inplace=True
            )

        # Keep personal details from the personal CSV.
        personal_columns = [
            "FirstName",
            "LastName",
            "ClassGrade",
            "Section",
            "Stream"
        ]

        duplicate_columns = [
            col for col in personal_columns
            if col in personal.columns and col in grades.columns
        ]

        grades.drop(
            columns=duplicate_columns,
            inplace=True,
            errors="ignore"
        )

        # Merge personal details with marks.
        data = personal.merge(
            grades,
            on="StudentID",
            how="left",
            validate="one_to_many"
        )

        # Normalize column names one final time.
        data.columns = data.columns.str.strip()

        # Ensure the columns required by the marksheet exist.
        required_columns = [
            "FirstName",
            "LastName",
            "ClassGrade",
            "Section"
        ]

        missing_columns = [
            col for col in required_columns
            if col not in data.columns
        ]

        if missing_columns:
            console.print(
                f"[red]Error: Required columns are missing: "
                f"{', '.join(missing_columns)}[/red]"
            )
            return None

        # Convert marks and attendance to numeric values where applicable.
        numeric_columns = [
            "AttendancePercent",
            "Total",
            "MaxPossible",
            "Percentage",
            "GPA"
        ]

        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors="coerce")

        return data

    except Exception as e:
        console.print(f"[red]Error loading student data: {e}[/red]")
        return None


# =========================================================
# SQLITE DATABASE
# =========================================================

def save_database(data):
    with sqlite3.connect(DATABASE_FILE) as connection:
        data.to_sql(
            "student_records",
            connection,
            if_exists="replace",
            index=False,
        )

    show_message("Student data saved to SQLite.", "green")


# =========================================================
# TERMINAL TABLES
# =========================================================

def display_table(data, title="STUDENT RECORDS"):
    if data.empty:
        show_message("No records found.", "yellow")
        return

    console.print(
        f"\n[bold bright_cyan]{title}[/bold bright_cyan]"
        f" [dim]({len(data)} records)[/dim]\n"
    )

    # Ask which columns to display when the dataset is wide.
    default_columns = [
        column
        for column in [
            "StudentID",
            "FirstName",
            "LastName",
            "Gender",
            "ClassGrade",
            "Section",
            "GPA",
            "AttendancePercent",
            "Percentage",
            "OverallGrade",
            "Status",
        ]
        if column in data.columns
    ]

    table = Table(
        box=box.ROUNDED,
        header_style="bold bright_cyan",
        border_style="blue",
        show_lines=False,
        expand=True,
    )

    for column in default_columns:
        table.add_column(column, overflow="fold")

    for _, row in data[default_columns].iterrows():
        values = []

        for column in default_columns:
            value = row[column]

            if pd.isna(value):
                display_value = "-"
            elif column in ["GPA", "AttendancePercent", "Percentage"]:
                display_value = f"{value:.2f}"
                if column in ["AttendancePercent", "Percentage"]:
                    display_value += "%"
            else:
                display_value = str(value)

            if column == "Status":
                style = "green" if display_value.lower() == "active" else "yellow"
                values.append(f"[{style}]{display_value}[/{style}]")
            else:
                values.append(display_value)

        table.add_row(*values)

    console.print(table)

    if len(data.columns) > len(default_columns):
        console.print(
            "[dim]Tip: Other fields are available in the student profile.[/dim]"
        )


def display_profile(records):
    if records.empty:
        show_message("Student not found.", "yellow")
        return

    row = records.iloc[0]

    table = Table(
        title=f"STUDENT PROFILE — {row['StudentID']}",
        box=box.ROUNDED,
        border_style="bright_cyan",
        header_style="bold bright_cyan",
        expand=True,
    )

    table.add_column("Field", style="yellow", ratio=1)
    table.add_column("Value", style="white", ratio=2)

    for column, value in row.items():
        if pd.isna(value):
            value = "-"

        table.add_row(str(column), str(value))

    console.print(table)

    if len(records) > 1:
        console.print("\n[bold bright_magenta]Academic records[/bold bright_magenta]")
        display_table(records, "STUDENT EXAM RECORDS")


# =========================================================
# SEARCH AND FILTER
# =========================================================

def search_student(data, query):
    query = query.strip()

    if not query:
        return data.iloc[0:0]

    columns = [
        column
        for column in ["StudentID", "FirstName", "LastName", "Email", "PhoneNumber"]
        if column in data.columns
    ]

    mask = pd.Series(False, index=data.index)

    for column in columns:
        mask |= data[column].astype(str).str.contains(
            query,
            case=False,
            na=False,
            regex=False,
        )

    return data[mask]


def get_student_records(data, student_id):
    return data[
        data["StudentID"].astype(str).str.strip().str.upper()
        == student_id.strip().upper()
    ]


def filter_students(data):
    console.print("\n[bold bright_cyan]FILTER STUDENT RECORDS[/bold bright_cyan]")

    columns = list(data.columns)

    for index, column in enumerate(columns, start=1):
        console.print(f"[yellow]{index:>2}.[/yellow] {column}")

    choice = IntPrompt.ask(
        "\nSelect column number",
        choices=[str(number) for number in range(1, len(columns) + 1)],
    )

    column = columns[choice - 1]
    value = Prompt.ask(f"Enter a value to search in '{column}'")

    result = data[
        data[column].astype(str).str.contains(
            value,
            case=False,
            na=False,
            regex=False,
        )
    ]

    display_table(result, f"FILTERED BY {column}")


# =========================================================
# MARKSHEET
# =========================================================

def view_marksheet(data, student_id):
    records = get_student_records(data, student_id)

    if records.empty:
        show_message("Student not found.", "red")
        return

    row = records.iloc[0]

    console.print(
        Panel(
            f"[bold bright_cyan]STUDENT MARKSHEET[/bold bright_cyan]\n"
            f"[white]Name:[/white] {row['FirstName']} {row['LastName']}\n"
            f"[white]Student ID:[/white] {row['StudentID']}\n"
            f"[white]Class:[/white] {row['ClassGrade']}  "
            f"[white]Section:[/white] {row['Section']}\n"
            f"[white]Exam:[/white] {row.get('ExamTerm', '-')}",
            border_style="bright_magenta",
        )
    )

    table = Table(box=box.ROUNDED, border_style="blue", expand=True)
    table.add_column("Subject", style="bright_cyan")
    table.add_column("Marks", justify="right", style="white")

    for subject in SUBJECTS:
        if subject in records.columns and pd.notna(row[subject]):
            table.add_row(subject, f"{row[subject]:g}")

    console.print(table)

    console.print(
        Panel(
            f"Total: [bold]{row.get('Total', '-')}[/bold] / "
            f"{row.get('MaxPossible', '-')}\n"
            f"Percentage: [bold bright_green]{row.get('Percentage', '-')}%[/bold bright_green]\n"
            f"Overall Grade: [bold bright_magenta]{row.get('OverallGrade', '-')}[/bold bright_magenta]\n"
            f"GPA: [bold]{row.get('GPA', '-')}[/bold]",
            title="RESULT SUMMARY",
            border_style="green",
        )
    )


# =========================================================
# ACADEMIC ANALYSIS
# =========================================================

def academic_analysis(data):
    students = data.drop_duplicates("StudentID").copy()

    total_students = len(students)
    active_count = (
        students["Status"].astype(str).str.lower().eq("active").sum()
        if "Status" in students.columns else 0
    )

    average_gpa = (
        students["GPA"].mean()
        if "GPA" in students.columns else float("nan")
    )

    average_attendance = (
        students["AttendancePercent"].mean()
        if "AttendancePercent" in students.columns else float("nan")
    )

    average_percentage = (
        students["Percentage"].mean()
        if "Percentage" in students.columns else float("nan")
    )

    table = Table(
        title="ACADEMIC OVERVIEW",
        box=box.DOUBLE,
        border_style="bright_cyan",
        expand=True,
    )

    table.add_column("Metric", style="bright_cyan")
    table.add_column("Value", justify="right", style="bright_green")

    table.add_row("Total Students", str(total_students))
    table.add_row("Active Students", str(active_count))
    table.add_row(
        "Average GPA",
        f"{average_gpa:.2f}" if pd.notna(average_gpa) else "N/A",
    )
    table.add_row(
        "Average Attendance",
        f"{average_attendance:.2f}%" if pd.notna(average_attendance) else "N/A",
    )
    table.add_row(
        "Average Exam Percentage",
        f"{average_percentage:.2f}%" if pd.notna(average_percentage) else "N/A",
    )

    console.print(table)

    if "OverallGrade" in data.columns:
        grade_table = Table(
            title="GRADE SUMMARY",
            box=box.ROUNDED,
            border_style="magenta",
        )

        grade_table.add_column("Grade", style="bright_cyan")
        grade_table.add_column("Number of Records", justify="right")

        for grade, count in data["OverallGrade"].value_counts().items():
            grade_table.add_row(str(grade), str(count))

        console.print(grade_table)


# =========================================================
# INTERACTIVE MATPLOTLIB GRAPHS
# =========================================================

def view_graphs(data):
    while True:
        console.print(
            Panel(
                "[1] Grade Distribution\n"
                "[2] Male vs Female Performance\n"
                "[3] Subject-wise Average Marks\n"
                "[4] Attendance vs Percentage\n"
                "[5] Top 10 Students\n"
                "[6] GPA Distribution\n"
                "[7] Pass vs Fail (if pass/fail data is available)\n"
                "[0] Back",
                title="[bold bright_cyan]INTERACTIVE GRAPH MENU[/bold bright_cyan]",
                border_style="bright_magenta",
            )
        )

        choice = Prompt.ask(
            "Choose a graph",
            choices=["0", "1", "2", "3", "4", "5", "6", "7"],
        )

        if choice == "0":
            break

        fig, ax = plt.subplots(figsize=(11, 6))
        fig.patch.set_facecolor("#111827")
        ax.set_facecolor("#172033")

        ax.tick_params(colors="white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("#67e8f9")

        for spine in ax.spines.values():
            spine.set_color("#64748b")

        ax.grid(color="#334155", linestyle="--", alpha=0.5)

        if choice == "1":
            if "OverallGrade" not in data.columns:
                plt.close(fig)
                show_message("OverallGrade column not found.", "yellow")
                continue

            counts = data.drop_duplicates("StudentID")["OverallGrade"].value_counts()
            bars = ax.bar(counts.index.astype(str), counts.values)

            ax.set_title("Student Grade Distribution")
            ax.set_xlabel("Overall Grade")
            ax.set_ylabel("Number of Students")

            mplcursors.cursor(bars, hover=True)

        elif choice == "2":
            if not {"Gender", "Percentage"}.issubset(data.columns):
                plt.close(fig)
                show_message("Gender or Percentage column not found.", "yellow")
                continue

            students = data.drop_duplicates("StudentID").copy()
            students["Percentage"] = pd.to_numeric(
                students["Percentage"], errors="coerce"
            )

            averages = students.groupby("Gender")["Percentage"].mean().dropna()
            bars = ax.bar(
                averages.index.astype(str),
                averages.values,
                color=["#22d3ee", "#f472b6", "#a78bfa", "#4ade80"][:len(averages)],
            )

            ax.set_title("Average Exam Percentage by Gender")
            ax.set_xlabel("Gender")
            ax.set_ylabel("Average Percentage (%)")

            mplcursors.cursor(bars, hover=True)

        elif choice == "3":
            available = [subject for subject in SUBJECTS if subject in data.columns]

            if not available:
                plt.close(fig)
                show_message("No subject columns found.", "yellow")
                continue

            averages = data[available].mean(numeric_only=True).dropna()
            bars = ax.bar(
                averages.index,
                averages.values,
                color="#2dd4bf",
            )

            ax.set_title("Subject-wise Average Marks")
            ax.set_xlabel("Subject")
            ax.set_ylabel("Average Marks")
            ax.tick_params(axis="x", labelrotation=35)

            mplcursors.cursor(bars, hover=True)

        elif choice == "4":
            required = {"AttendancePercent", "Percentage"}

            if not required.issubset(data.columns):
                plt.close(fig)
                show_message("Attendance or Percentage column not found.", "yellow")
                continue

            students = data.drop_duplicates("StudentID").copy()

            students["AttendancePercent"] = pd.to_numeric(
                students["AttendancePercent"], errors="coerce"
            )
            students["Percentage"] = pd.to_numeric(
                students["Percentage"], errors="coerce"
            )

            points = students[
                ["AttendancePercent", "Percentage"]
            ].dropna()

            if points.empty:
                plt.close(fig)
                show_message("No valid attendance and percentage data.", "yellow")
                continue

            scatter = ax.scatter(
                points["AttendancePercent"],
                points["Percentage"],
                color="#c084fc",
                alpha=0.85,
                s=65,
            )

            ax.set_title("Attendance vs Exam Percentage")
            ax.set_xlabel("Attendance (%)")
            ax.set_ylabel("Exam Percentage (%)")

            cursor = mplcursors.cursor(scatter, hover=True)
            cursor.connect(
                "add",
                lambda selection, frame=points: selection.annotation.set_text(
                    f"Attendance: {frame.iloc[selection.index]['AttendancePercent']:.1f}%\n"
                    f"Percentage: {frame.iloc[selection.index]['Percentage']:.1f}%"
                ),
            )

        elif choice == "5":
            if "Percentage" not in data.columns:
                plt.close(fig)
                show_message("Percentage column not found.", "yellow")
                continue

            students = data.drop_duplicates("StudentID").copy()
            students["Percentage"] = pd.to_numeric(
                students["Percentage"], errors="coerce"
            )

            top = students.nlargest(10, "Percentage").dropna(
                subset=["Percentage"]
            )

            if top.empty:
                plt.close(fig)
                show_message("No valid percentage data.", "yellow")
                continue

            top["StudentName"] = (
                top["FirstName"].astype(str)
                + " "
                + top["LastName"].astype(str)
            )

            bars = ax.barh(
                top["StudentName"].iloc[::-1],
                top["Percentage"].iloc[::-1],
                color="#fbbf24",
            )

            ax.set_title("Top 10 Students by Exam Percentage")
            ax.set_xlabel("Percentage (%)")
            ax.set_ylabel("Student")

            mplcursors.cursor(bars, hover=True)

        elif choice == "6":
            if "GPA" not in data.columns:
                plt.close(fig)
                show_message("GPA column not found.", "yellow")
                continue

            students = data.drop_duplicates("StudentID")
            gpa = pd.to_numeric(students["GPA"], errors="coerce").dropna()

            if gpa.empty:
                plt.close(fig)
                show_message("No valid GPA data.", "yellow")
                continue

            ax.hist(gpa, bins="auto", color="#60a5fa", edgecolor="white")
            ax.set_title("GPA Distribution")
            ax.set_xlabel("GPA")
            ax.set_ylabel("Number of Students")

        elif choice == "7":
            show_message(
                "Your sample contains no explicit pass/fail column. "
                "Add a confirmed pass/fail rule before using this graph.",
                "yellow",
            )
            plt.close(fig)
            continue

        fig.tight_layout()
        plt.show()


# =========================================================
# CSV AND EXCEL EXPORT
# =========================================================

def export_csv(data):
    filename = Prompt.ask(
        "Enter CSV filename",
        default="student_report.csv",
    )

    if not filename.lower().endswith(".csv"):
        filename += ".csv"

    output = BASE_DIR / Path(filename).name
    data.to_csv(output, index=False)

    show_message(f"CSV exported to: {output}")


def export_excel(data):
    filename = Prompt.ask(
        "Enter Excel filename",
        default="student_report.xlsx",
    )

    if not filename.lower().endswith(".xlsx"):
        filename += ".xlsx"

    output = BASE_DIR / Path(filename).name

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        data.to_excel(writer, index=False, sheet_name="Student Records")

        if "OverallGrade" in data.columns:
            data["OverallGrade"].value_counts().rename_axis(
                "Grade"
            ).reset_index(
                name="Count"
            ).to_excel(
                writer,
                index=False,
                sheet_name="Grade Summary",
            )

    show_message(f"Excel exported to: {output}")


# =========================================================
# PDF MARKSHEET
# =========================================================

def generate_pdf_marksheet(data, student_id):
    records = get_student_records(data, student_id)

    if records.empty:
        show_message("Student not found.", "yellow")
        return

    row = records.iloc[0]

    safe_id = "".join(
        character if character.isalnum() or character in "-_"
        else "_"
        for character in student_id
    )

    output = REPORT_DIR / f"marksheet_{safe_id}.pdf"

    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
    )

    styles = getSampleStyleSheet()

    elements = [
        Paragraph("STUDENT ACADEMIC MARKSHEET", styles["Title"]),
        Spacer(1, 15),
        Paragraph(
            f"Student ID: {row['StudentID']}<br/>"
            f"Student Name: {row['FirstName']} {row['LastName']}<br/>"
            f"Class: {row['ClassGrade']}<br/>"
            f"Section: {row['Section']}<br/>"
            f"Exam: {row.get('ExamTerm', '-')}",
            styles["Normal"],
        ),
        Spacer(1, 20),
    ]

    table_data = [["Subject", "Marks"]]

    for subject in SUBJECTS:
        if subject in records.columns and pd.notna(row[subject]):
            table_data.append([subject, str(row[subject])])

    table = PDFTable(table_data, colWidths=[300, 100], repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123456")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            f"Total: {row.get('Total', '-')} / {row.get('MaxPossible', '-')}<br/>"
            f"Percentage: {row.get('Percentage', '-')}%<br/>"
            f"Overall Grade: {row.get('OverallGrade', '-')}<br/>"
            f"GPA: {row.get('GPA', '-')}",
            styles["Heading2"],
        )
    )

    document.build(elements)

    show_message(f"PDF marksheet created: {output}")


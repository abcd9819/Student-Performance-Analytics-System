
from rich.prompt import Prompt
from rich.panel import Panel

from functions import (
    console,
    show_title,
    show_menu,
    show_message,
    pause,
    load_data,
    save_database,
    display_table,
    display_profile,
    search_student,
    get_student_records,
    filter_students,
    view_marksheet,
    academic_analysis,
    view_graphs,
    export_csv,
    export_excel,
    generate_pdf_marksheet,
)


def main():
    show_title()

    try:
        data = load_data()
        save_database(data)

    except Exception as error:
        console.print(
            Panel(
                f"[bold red]Unable to load student data[/bold red]\n\n{error}",
                border_style="red",
            )
        )
        return

    while True:
        show_title()

        # One record per student for summary cards.
        students = data.drop_duplicates("StudentID")

        average_gpa = (
            students["GPA"].mean()
            if "GPA" in students.columns else None
        )

        average_attendance = (
            students["AttendancePercent"].mean()
            if "AttendancePercent" in students.columns else None
        )

        console.print(
            Panel(
                f"[bold cyan]Total Students:[/bold cyan] {len(students)}\n"
                f"[bold green]Average GPA:[/bold green] "
                f"{average_gpa:.2f}" if average_gpa is not None else
                f"[bold cyan]Total Students:[/bold cyan] {len(students)}",
                title="QUICK OVERVIEW",
                border_style="bright_blue",
            )
        )

        if average_attendance is not None:
            console.print(
                f"[bright_magenta]Average Attendance:[/bright_magenta] "
                f"{average_attendance:.2f}%\n"
            )

        show_menu()

        choice = Prompt.ask(
            "\n[bold bright_yellow]Select an option[/bold bright_yellow]",
            choices=[
                "0", "1", "2", "3", "4", "5",
                "6", "7", "8", "9", "10", "11"
            ],
        )

        try:
            if choice == "1":
                display_table(data, "ALL STUDENT RECORDS")

            elif choice == "2":
                query = Prompt.ask("Enter student ID or name")
                results = search_student(data, query)
                display_table(results, "SEARCH RESULTS")

            elif choice == "3":
                student_id = Prompt.ask("Enter Student ID").strip().upper()
                records = get_student_records(data, student_id)
                display_profile(records)

            elif choice == "4":
                student_id = Prompt.ask("Enter Student ID").strip().upper()
                view_marksheet(data, student_id)

            elif choice == "5":
                filter_students(data)

            elif choice == "6":
                academic_analysis(data)

            elif choice == "7":
                view_graphs(data)

            elif choice == "8":
                export_csv(data)

            elif choice == "9":
                export_excel(data)

            elif choice == "10":
                student_id = Prompt.ask("Enter Student ID").strip().upper()
                generate_pdf_marksheet(data, student_id)

            elif choice == "11":
                data = load_data()
                save_database(data)
                show_message("Dataset reloaded successfully.")

            elif choice == "0":
                console.print(
                    Panel(
                        "[bold bright_cyan]Thank you for using "
                        "Student Analytical System![/bold bright_cyan]",
                        border_style="bright_magenta",
                    )
                )
                break

        except Exception as error:
            show_message(f"Operation failed: {error}", "red")

        pause()


if __name__ == "__main__":
    main()


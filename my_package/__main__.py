from datetime import datetime
from typing import List


class Developer:
    valid_languages: List[str] = [
        "Python",
        "Java",
        "JavaScript",
        "C",
        "C++",
        "C#",
        "PHP",
        "Swift",
        "Go",
        "Kotlin",
        "Ruby",
        "Rust",
        "TypeScript",
        "Scala",
        "Perl",
        "Lua",
        "Groovy",
        "R",
        "Shell",
        "Objective-C",
        "SQL",
        "HTML/CSS",
    ]

    def __init__(self, name, language) -> None:
        if language not in self.valid_languages:
            raise ValueError(f"{language} is not a valid language.")
        self.name = name
        self.language = language

    def get_info(self) -> str:
        return f"{self.name} is a developer who codes in {self.language}."


def start_coding() -> None:
    print("Get ready to extract some data!")


def date() -> datetime:
    current_datetime: datetime = datetime.now()
    return current_datetime


def main() -> None:
    start_coding()
    print(date())
    dev = Developer("Rinse", "Python")
    print(dev.get_info())


main()


def run_extraction_cli() -> None:
    import argparse

    from my_package.flows.extraction_flow import prospectus_extraction_flow

    parser = argparse.ArgumentParser(description="Run the prospectus extraction flow.")
    parser.add_argument("--source-dir", default="prospect documents")
    parser.add_argument("--output-dir", default="extraction_output")
    args = parser.parse_args()
    prospectus_extraction_flow(source_dir=args.source_dir, output_dir=args.output_dir)


if __name__ == "__main__":
    run_extraction_cli()

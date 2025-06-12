import typing
import pathlib
import requests
import bs4
import dataclasses
import enum
import decimal
import re
import pprint

def _tag(obj: typing.Any) -> bs4.Tag:
    assert isinstance(obj, bs4.Tag)
    return obj
tag = _tag

@dataclasses.dataclass
class Note:
    label: str
    text: str

    @staticmethod
    def from_tag(tag: bs4.Tag) -> "Note":
        label = _tag(tag.b).text
        text = tag.text
        return Note(label, text)

    @staticmethod
    def from_doc(doc: bs4.Tag) -> list["Note"]:
        notes: list[Note] = []
        for note in map(tag, doc("li", recursive=False)):
            notes.append(Note.from_tag(note))
        return notes

@dataclasses.dataclass
class CourseLabel:
    code: str
    name: str

    @staticmethod
    def from_txt(coursename: str):
        return CourseLabel(*coursename.split(maxsplit=1))

class ModuleType(enum.StrEnum):
    EXAM = "Tentamen"
    PROJECT = "Projekt"
    ASSIGNMENT = "Inlämningsuppgift"
    HOME_EXAM = "Hemtentamen"
    LAB = "Laboration"
    DUGGA = "Dugga"
    WORK_A = "Examensarbete (del A)"
    WORK_B = "Examensarbete (del B)"
    WORK = "Examensarbete"

    @staticmethod
    def from_text(txt: str) -> "ModuleType":
        for member in ModuleType:
            if member.value == txt:
                return member
        raise ValueError("invalid module type name: " + txt)


@dataclasses.dataclass
class CourseModuleInfo:
    variant: ModuleType
    points: decimal.Decimal

    @staticmethod
    def from_text(txt: str) -> "CourseModuleInfo":
        module_type, points, hp = txt.rsplit(maxsplit=2)
        assert hp == "hp", "invalid course module format format (missing hp)"
        return CourseModuleInfo(ModuleType.from_text(module_type), decimal.Decimal(points.replace(",", ".")))

class BlockType(enum.StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"

class ExamDay(enum.StrEnum):
    Monday = "Må"
    Tuesday = "Ti"
    Wednesday = "On"
    Thursday = "To"
    Friday = "Fr"
    Saturday = "Lö"

    @staticmethod
    def from_day(day: str) -> "ExamDay":
        for exam_day in ExamDay:
            if exam_day.value == day:
                return exam_day
        raise ValueError("invalid exam day: " + day)

class ExamPlace(enum.StrEnum):
    L = "Lindholmen"
    J = "Johanneberg"

_EXAM_DAYS = [day.value for day in ExamDay]
_EXAM_DATE = f"({'|'.join(_EXAM_DAYS)})" + r"\s+(\d+)/(\d+)-(\d+) (em|fm) " f"({'|'.join(p.name for p in ExamPlace)})" + r"(?: (DIG))?"
_EXAM = f"{_EXAM_DATE}|(Kontakta examinator)"
EXAM_RE = re.compile(f"^{_EXAM}$")



@dataclasses.dataclass
class ExamInfo:
    weekday: ExamDay
    day: int
    month: int
    year: int
    is_noon: bool
    place: ExamPlace
    is_digital: bool

    @staticmethod
    def parse(text: str) -> typing.Optional["ExamInfo"]:
        if (m := EXAM_RE.fullmatch(text)) is not None:
            weekday, day, month, year, tod, place, digital, contact = m.group(*range(1, 8+1))

            if contact is not None:
                return None
            return ExamInfo(
                ExamDay.from_day(weekday),
                int(day),
                int(month),
                int(year),
                tod == "fm",
                ExamPlace[place],
                digital is not None)
        raise ValueError("invalid format of exam info")
    
    @staticmethod
    def is_exam(exam: typing.Optional["ExamInfo"]) -> typing.TypeGuard["ExamInfo"]:
        return exam is not None

@dataclasses.dataclass
class CourseNode:
    label: CourseLabel
    module: CourseModuleInfo
    block: typing.Optional[BlockType]
    extended_block: bool
    notes: list[str]
    exam: list[ExamInfo]
    reexam: list[ExamInfo]

    @staticmethod
    def from_doc(doc: bs4.Tag) -> "CourseNode":
        name, module, block, notes, exam, reexam = map(tag, doc.children)
        block_s: typing.Optional[str] = tag(block.button).text if block.button is not None else None
        notes_s: list[str] = notes.text.split(", ")
        exams = filter(ExamInfo.is_exam, map(ExamInfo.parse, [tag(e).text for e in exam("li")]))
        reexams = filter(ExamInfo.is_exam, map(ExamInfo.parse, [tag(e).text for e in reexam("li")]))
        return CourseNode(
            CourseLabel.from_txt(tag(name.a).text),
            CourseModuleInfo.from_text(module.text),
            BlockType[block_s.removesuffix("+")] if block_s is not None else None,
            block_s.endswith("+") if block_s is not None else False,
            notes_s,
            list(exams),
            list(reexams)
        )

@dataclasses.dataclass
class PeriodInfo:
    name: str
    mandatory_courses: list[CourseNode]
    optional_courses: list[CourseNode]

    @staticmethod
    def from_doc(doc: bs4.Tag) -> "PeriodInfo":
        info = PeriodInfo(tag(doc.h3).text, [],[])
        for course_list in map(tag, tag(doc.ul).children):
            title = tag(course_list.h4).text
            is_optional = title == "Valbara kurser"
            courses = map(tag, tag(course_list.find("tbody")).children)
            for course in courses:
                course_node = CourseNode.from_doc(course)
                if is_optional: info.optional_courses.append(course_node)
                else: info.mandatory_courses.append(course_node)
        return info
    
    @staticmethod
    def from_final_project_doc(doc: bs4.Tag) -> "PeriodInfo":
        info = PeriodInfo(tag(doc.h2).text, [], [])
        courses = map(tag, tag(doc.find("tbody")).children)
        for course in courses:
            course_node = CourseNode.from_doc(course)
            info.mandatory_courses.append(course_node)
        return info



@dataclasses.dataclass
class ProgrammeOverview:
    periods: list[PeriodInfo]
    notes: list[Note]

    @staticmethod
    def fetch(url: str, is_path: bool = False) -> "ProgrammeOverview":
        if is_path:
            doc = pathlib.Path(url).read_text(encoding="utf-8")
        else:
            r = requests.get(url)
            r.raise_for_status()
            doc = r.text

        soup = bs4.BeautifulSoup(doc, "html.parser")
        root_article = tag(soup.find("article"))

        terms, notes = map(tag, root_article.find_all("ul", recursive=False))
        notes = Note.from_doc(notes)

        all_periods = []
        for term in map(tag, terms.children):
            name = tag(term.h2).text
            if name == "Examensarbete":
                all_periods.append(PeriodInfo.from_final_project_doc(term))
            else:
                all_periods.extend(PeriodInfo.from_doc(tag(pi)) for pi in tag(term.ul).children)
        return ProgrammeOverview(all_periods, notes)


def generate_document(path: pathlib.Path, overviews: list[ProgrammeOverview]):
    # TODO: placeholder, this should actually output to a DB
    with path.open("w", encoding="utf-8") as fp:
        pprint.pprint(overviews, fp)

if __name__ == "__main__":
    import argparse
    import sys
    import string

    parser = argparse.ArgumentParser(sys.argv[0], description="fetch program plans from \"any\" university...")
    parser.add_argument("format", type=str, help="A format string containing the variable $year (see --year)")
    parser.add_argument("-y", "--years", type=lambda s: map(int, s.split(",")), default=[1], help="The years to fetch, seperated by ','")
    parser.add_argument("-o", "--output", type=pathlib.Path, default="programme.csv", help="output csv file")
    parser.add_argument("--is-path", action="store_true", help="if the url points to a path")

    args = parser.parse_args()

    urlf = string.Template(args.format)
    years: list[int] = args.years
    output: pathlib.Path = args.output
    is_path: bool = args.is_path

    urls = [urlf.substitute({"year": year}) for year in years]
    all_years = [ProgrammeOverview.fetch(url, is_path) for url in urls]

    generate_document(output, all_years)

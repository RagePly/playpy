import bs4
import requests
import pathlib
import typing
import dataclasses
import re
import datetime
import sys

## Configuration ##

UNITS = [
    "tsk",
    "msk",
    "dl",
    "kvist",
    "kvistar",
    "kruka",
    "krukor",
    "kg",
    "g",
]
LEFT_MARKER = "| "
INTERSPERSE_MARKER = " | "
RIGHT_MARKER = " |"

TITLE = "Köket.se Ingrediensutskrift"
NAME_TITLE = "Ingrediens"
AMOUNT_TITLE = "Mängd"
UNIT_TITLE = "Enhet"

AMOUNT_UNIT_NAME_RE = re.compile(r"^(\d+(?:,\d+)?)\s+" + f"({'|'.join(UNITS)})" r"\s+(.*)$")
AMOUNT_ST_NAME_RE  = re.compile(r"^(\d+(?:,\d+)?)\s+(.*)$")

## Helpers ##

def int_or_float(t: str) -> int | float:
    try: return int(t)
    except: return float(t.replace(",", "."))
def starts_with(start: str) -> typing.Callable[[str | None], bool]:
    def _check(s: str | None): return s is not None and s.startswith(start)
    return _check

def is_tag(value: typing.Any) -> typing.TypeGuard[bs4.Tag]:
    return isinstance(value, bs4.Tag)

## Ingredient class ##

@dataclasses.dataclass
class IngredientEntry:
    amount: int | float | None
    unit: str | None
    name: str

    @staticmethod
    def parse(text: str) -> "IngredientEntry":
        if (m := AMOUNT_UNIT_NAME_RE.fullmatch(text)) is not None:
            return IngredientEntry(int_or_float(m[1]), m[2], m[3])
        elif (m := AMOUNT_ST_NAME_RE.fullmatch(text)) is not None:
            return IngredientEntry(int_or_float(m[1]), "st", m[2])
        return IngredientEntry(None, None, text)

Ingredients: typing.TypeAlias = dict[str | None, list[IngredientEntry]]

## Data processing ##

def fetch_strategy_online(url: str) -> str:
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text

def handle_ingredients(ingredients: bs4.Tag) -> list[IngredientEntry]:
    entries = []
    for entry in ingredients.find_all(class_ = starts_with("ingredient_ingredient")):
        assert is_tag(entry), "expected all ingredient-entries to be tags"
        entry_text = entry.string
        assert entry_text is not None, "expected ingredient-entry to contain text"
        entries.append(IngredientEntry.parse(entry_text))
    return entries

def handle_document(parser: bs4.BeautifulSoup) -> Ingredients:
    ingredient_wrapper = parser.find(id="ingredients")
    assert isinstance(ingredient_wrapper, bs4.Tag)
    ingredient_lists: Ingredients = {}
    for ingredients in ingredient_wrapper.children:
        assert is_tag(ingredients), "expected tag"
        title_tag = ingredients.find(class_ = starts_with("ingredients_list_sectionTitle"))
        title = title_tag.string if is_tag(title_tag) else None

        assert not (title is None and None in ingredient_lists), "two unnamed titles were not expected"
        ingredient_lists[title] = handle_ingredients(ingredients)
    return ingredient_lists

## Output-formatting ##

def get_width_of_col(name: str, ingredients: Ingredients) -> int:
    max_width = len(name)
    for collection in ingredients.values():
        for cell in collection:
            value = getattr(cell, name)
            if value is None:
                continue
            else:
                max_width = max(max_width, len(str(value)))
    return max_width

def get_widths(ingredients: Ingredients) -> tuple[int, int, int]:
    name_width = max(len(NAME_TITLE), get_width_of_col("name", ingredients))
    amount_width = max(len(AMOUNT_TITLE), get_width_of_col("amount", ingredients))
    unit_width = max(len(UNIT_TITLE), get_width_of_col("unit", ingredients))
    return name_width, amount_width, unit_width

def get_total_width(ingredients: Ingredients) -> int:
    markup_width = sum(map(len, [LEFT_MARKER, INTERSPERSE_MARKER * 2, RIGHT_MARKER]))
    name_width, amount_width, unit_width = get_widths(ingredients)
    return markup_width + name_width + amount_width + unit_width

def write_title(ingredients: Ingredients, title: str):
    title = f"** {title.capitalize()} **" if title else ""
    total_width = get_total_width(ingredients)
    remaining_width = total_width - len(title)
    return title.rjust(remaining_width // 2 + len(title))

def write_header(ingredients: Ingredients) -> str:
    name_width, amount_width, unit_width = get_widths(ingredients)
    return LEFT_MARKER + \
        NAME_TITLE.ljust(name_width) + INTERSPERSE_MARKER + \
        AMOUNT_TITLE.ljust(amount_width) + INTERSPERSE_MARKER + \
        UNIT_TITLE.ljust(unit_width) + RIGHT_MARKER

def write_seperator(ingredients: Ingredients) -> str:
    name_width, amount_width, unit_width = get_widths(ingredients)
    return LEFT_MARKER + \
        "-"*name_width + INTERSPERSE_MARKER + \
        "-"*amount_width + INTERSPERSE_MARKER + \
        "-"*unit_width + RIGHT_MARKER

def write_collection(ingredients: Ingredients) -> typing.Generator[str]:
    name_width, amount_width, unit_width = get_widths(ingredients)

    for i, (collection, ingredient_list) in enumerate(ingredients.items()):
        if i != 0: yield ""

        if collection is not None:
            yield write_title(ingredients, collection)
        yield write_header(ingredients)
        yield write_seperator(ingredients)

        for entry in ingredient_list:
            name = entry.name or ""
            amount = str(entry.amount) if entry.amount is not None else ""
            unit = str(entry.unit) if entry.unit is not None else ""
            yield LEFT_MARKER + \
                name.ljust(name_width) + INTERSPERSE_MARKER + \
                amount.rjust(amount_width) + INTERSPERSE_MARKER + \
                unit.ljust(unit_width) + RIGHT_MARKER

def create_report(url: str) -> typing.Generator[str]:
    document = fetch_strategy_online(url)
    parser = bs4.BeautifulSoup(document, "html.parser")

    # Get author name
    author = parser.find(class_ = starts_with("author_wrapper"))
    assert is_tag(author)
    author_text = author.p.span.a.string or ""

    # Get recipy title
    title = parser.find(class_ = starts_with("recipe_title"))
    assert is_tag(title)
    title_text = title.string or ""

    ingredients = handle_document(parser)
    now = datetime.datetime.today()
    yield TITLE
    yield f"Address: {url}"
    yield f"Recept:  {title_text}"
    yield f"Av:      {author_text}"
    yield f"Datum:   {now.strftime('%Y/%m/%d %H:%M:%S')}"
    yield ""
    yield from write_collection(ingredients)

if __name__ == "__main__":
    # document = fetch_strategy_file("res/potatis.html")
    match sys.argv:
        case [_, url]:
            print("\n".join(create_report(url)))
            exit(0)
        case [prog, *_]:
            print(f"usage: python {prog} URL", file=sys.stderr)
            exit(1)
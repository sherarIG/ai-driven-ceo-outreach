from pathlib import Path
import textwrap

_CEO_BRIEF_PATH = Path(__file__).with_name("ceo_brief.txt")

# ► specify encoding and ignore bad bytes if any
CEO_BRIEF = textwrap.dedent(
    _CEO_BRIEF_PATH.read_text(encoding="utf-8", errors="replace")
).strip()


def get_row_block(person_name: str,
                  company: str,
                  role: str,
                  relationship: str,
                  notes: str) -> str:
    """
    Format the row-specific inputs in a compact, tagged block.
    """
    return textwrap.dedent(f"""\
        <Contact_Name>{person_name}</Contact_Name>
        <Company>{company}</Company>
        <Role>{role}</Role>
        <Relationship>{relationship}</Relationship>
        <Notes>{notes}</Notes>
    """).strip()


def build_messages(person_name: str,
                   company: str,
                   role: str,
                   relationship: str,
                   notes: str):
    """
    Return the messages array for the Chat Completions call.
    """
    row_block = get_row_block(person_name, company, role, relationship, notes)

    # System message – model sees it first every call
    system_msg = (
        CEO_BRIEF
        + "\n\nYou are Jason's AI outreach assistant. "
        "When you answer, you MUST return ONLY a valid JSON object with exactly these keys: "
        "Person_Name, Company, Suggested_Email."
    )

    # User message – row-specific fields + explicit output example
    user_msg = (
        f"{row_block}\n\n###\n"
        "Produce one JSON object following this example:\n"
        '{"Person_Name": "Ada Lovelace", "Company": "Analytical Engines", '
        '"Suggested_Email": "ada@analyticalengines.com"}'
    )

    return [
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": user_msg},
    ]



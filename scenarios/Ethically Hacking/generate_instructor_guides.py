"""Generate instructor guide Word documents for the FSSCP scenario modules.

Run from the repository root:

    python scripts/generate_instructor_guides.py

Each guide is written next to its scenario JSON. The questions and answers section is
built from the JSON at generation time, so the answer key cannot drift from the scenario
the teams are actually scored against. Only the prose sections are authored by hand, in
MODULE_CONTENT below.

Documents are written as minimal WordprocessingML packages using the standard library,
so no third-party dependency is required.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = REPO_ROOT / "scenarios" / "Ethically Hacking"

# Prose written per module. Everything else in the guide is derived from the scenario JSON.
MODULE_CONTENT: dict[int, dict[str, object]] = {
    6: {
        "theme": "Operator Fundamentals",
        "purpose": [
            "Module 6 is the entry point to the FSSCP program and the only module with no "
            "adversary activity in it. Its job is to make every crew fluent with the operator "
            "terminal and confident reading spacecraft telemetry before anything starts going "
            "wrong to them.",
            "It also establishes the crew structure the later modules assume: three named roles, "
            "a single decision authority, and an agreed escalation path. Teams that leave this "
            "module without those habits tend to struggle once alerts and time pressure arrive.",
        ],
        "how_it_works": [
            "Each team is assigned an identical microsatellite in Earth orbit with three ground "
            "stations available. Contact is close to continuous, so crews are not fighting pass "
            "timing while they are still learning the interface. Link quality still varies with "
            "range and geometry, which is what makes the ground station comparison a real task "
            "rather than a lookup.",
            "Nothing is scripted to fail. There is no anomaly timeline, no cyber inject, and no "
            "third-party asset in the environment. Every answer is discoverable from live "
            "telemetry, imagery, the map, or the crew's own rules of engagement.",
            "Scored questions are delivered through the Tasks section of the operator terminal in "
            "three streams, one per crew role: Satellite Operations, Payload Operations and "
            "Mission Lead. Teams submit once per question and the question locks after "
            "submission, so guessing early has a real cost.",
        ],
        "instructor_notes": [
            "Confirm each team has filled the three crew roles before the session starts: "
            "Satellite Operator, Payload Operator and Mission Lead. Three of the scored "
            "questions are answered from the crew's own rules of engagement rather than from "
            "telemetry, so a crew that never agreed its structure has nothing to answer from.",
            "Push teams to read every task before they start commanding. Crews that jump straight "
            "into commanding routinely miss an observation they cannot go back for.",
            "Peak solar panel output is only observable once a crew deliberately changes pointing "
            "mode. A team that never repoints will under-report it and will usually blame the "
            "spacecraft rather than their own plan.",
            "The GPS data question is about knowing which views expose which data, not about a "
            "position value. Expect at least one team to over-select and score zero.",
            "Watch for teams treating the ground station comparison as a guess. Ask which "
            "telemetry they used before you confirm anything.",
        ],
    },
    7: {
        "theme": "Pass Operations and Earth Observation",
        "purpose": [
            "Module 7 moves crews out of the benign, continuously connected environment of "
            "Module 6 and into real pass discipline. The spacecraft is only reachable while a "
            "ground station has line of sight, so the crew has to decide what happens inside a "
            "contact window before that window opens.",
            "It is also the first module that scores collection work. Teams point a body-fixed "
            "camera at two widely separated maritime areas, get the imagery on the ground, and "
            "then judge whether what came back is good enough to report. Nothing here is "
            "adversarial. The difficulty is planning and self-discipline.",
        ],
        "how_it_works": [
            "Each team flies an imaging microsatellite in a low-inclination orbit with four "
            "ground stations spread around the globe. Stations need the spacecraft above a ten "
            "degree elevation mask, so contact arrives in discrete passes with real gaps between "
            "them. The session runs a little over one orbit, so each tasked area only comes back "
            "into reach a small number of times.",
            "Two maritime areas are tasked, one in the Strait of Malacca and one around Hawaii. "
            "Each holds a group of stationary vessels sharing a single hull colour. A cloud layer "
            "is modelled, so a pass can come back obscured and a crew may need more than one "
            "look. The camera shares its mounting face with the radios, which means pointing "
            "decisions affect imaging and communications together.",
            "Nothing is scripted to fail. The Mission Lead and Satellite Operations streams score "
            "how the crew runs a contact window, and the Payload Operations stream scores both "
            "the collection result and the crew's own product quality gate. Teams submit once per "
            "question and the question locks after submission.",
        ],
        "instructor_notes": [
            "The two collection areas are on opposite sides of the planet. Watch whether crews "
            "notice that early and plan for both, or burn their first passes on one area and run "
            "out of opportunities for the other.",
            "Cloud will cost some crews a pass, and that is intended. What matters is whether "
            "they recognise the capture is unusable and retask, rather than reporting it.",
            "Six of the ten questions are about how the crew runs a pass rather than what the "
            "telemetry says. Crews that never agree an acquisition and end-of-pass routine will "
            "be guessing.",
            "Expect crews to keep commanding into loss of signal on their first pass or two. Let "
            "it happen once, then ask them what they lost.",
            "The vessel counts are only answerable from imagery. If a crew asks you to confirm a "
            "count, send them back to their captures.",
        ],
    },
    8: {
        "theme": "Situation Reporting",
        "purpose": [
            "Module 8 is about reporting rather than flying. Crews run a similar Earth "
            "observation mission to Module 7, but the scored output is the quality of their "
            "situation reports: what they claim, what evidence sits behind each claim, and what "
            "they leave out.",
            "It also introduces the distinction the rest of the program depends on. Some of what "
            "a crew sees on the link and in its payload data points to interference or intrusion, "
            "and some of it is routine hardware health. Teams start sorting one from the other "
            "here, before anything is actually done to them.",
        ],
        "how_it_works": [
            "Each team flies an imaging microsatellite in a mid-inclination orbit with four "
            "widely separated ground stations, so contact again comes in passes with gaps between "
            "them. Two maritime areas are tasked, one in the Aegean Sea and one in the Tasman Sea "
            "between Australia and New Zealand, each holding a group of stationary vessels "
            "sharing a single hull colour.",
            "No anomaly is injected. Everything a crew reports has to come from live telemetry, "
            "imagery and its own command log. Satellite Operations is scored on where a link "
            "health claim comes from and which signatures would downgrade a status call. Payload "
            "Operations is scored on the collection result and the integrity checks applied "
            "before a product is released. The Mission Lead is scored on the merge: what earns a "
            "place in a single mission report and what belongs in an annex.",
            "Because nothing goes wrong on its own, the cyber questions here are hypothetical. "
            "Teams are asked which observations would indicate interference, not to detect one. "
            "Modules 9 and 10 make it real.",
        ],
        "instructor_notes": [
            "Set the report format expectation before the session starts. Crews that invent a "
            "format at the end lose passes to it.",
            "Push crews to name their source when they report link health. The most common "
            "failure in this module is a confident status call with nothing behind it.",
            "The Mission Lead questions reward cutting detail. Expect crews who worked hard on "
            "telemetry to resist dropping it, and use that tension in the debrief.",
            "Cloud can obscure a capture in this environment, so crews should budget for repeat "
            "looks over each sea.",
            "The two seas are roughly half a world apart and need separate pass planning. A crew "
            "that treats them as one task will be short of opportunities.",
        ],
    },
    9: {
        "theme": "Detect and Confirm",
        "purpose": [
            "Module 9 is the first module where things are done to the crew rather than by it. "
            "Alerts arise across the session and the crew has to work each one into a described, "
            "evidenced finding inside sixty seconds, without stopping the imagery tasking that is "
            "running alongside them.",
            "The lesson is the one in the title. An alert is not an incident. Some of what the "
            "crew sees is adversary activity and some of it is hardware failing on its own. A "
            "crew that escalates everything has failed the module just as surely as a crew that "
            "escalates nothing.",
        ],
        "how_it_works": [
            "Each team flies an imaging microsatellite in a high-inclination orbit with five "
            "ground stations, starting with the battery at half charge. Tasking covers a vessel "
            "group in the Caribbean east of Florida and another off the west coast of Peru, so "
            "payload work continues while alerts are live.",
            "Three things are scripted. Navigation is interfered with from the moment the session "
            "starts, so the position solution is already untrustworthy before the crew has taken "
            "a baseline. Text is injected into a downlinked telemetry packet around the half hour "
            "mark and expires on its own a little later. A reaction wheel jams during the second "
            "half of the session and returns to normal shortly afterwards without crew action.",
            "The scored questions follow that structure. Satellite Operations characterises and "
            "locates the navigation and telemetry findings, Payload Operations delivers the "
            "collection result and identifies the attitude problem, and the Mission Lead "
            "classifies each alert and decides what belongs in a cyber detection report.",
        ],
        "instructor_notes": [
            "Two of the three anomalies clear themselves. Crews that wait rather than investigate "
            "will watch the symptom disappear and may conclude nothing happened. Note who "
            "recorded an onset time and who did not.",
            "The navigation interference is running before the crew takes its baseline, so a crew "
            "that trusts its first reading has anchored to bad data. Watch for it and save it for "
            "the debrief.",
            "The wheel fault is the trap. It is a natural failure, and crews primed to hunt an "
            "attacker will fold it into their cyber report.",
            "Hold crews to the sixty second triage limit out loud. The point is a described "
            "finding under time pressure, not a complete diagnosis.",
            "The telemetry inject is only visible to a crew that inspects packet contents rather "
            "than plotted values. If nobody opens the raw data, nobody finds it.",
        ],
    },
    10: {
        "theme": "Respond and Recover",
        "purpose": [
            "Module 10 picks up where Module 9 stops. The activity is already confirmed as "
            "adversary action, so triage is not the exercise. Acting on it is: declare the "
            "incident, scope it, contain it, recover deliberately, and keep reporting throughout.",
            "It also tests restraint. A persistent hardware fault runs alongside the incident, "
            "and the temptation is either to fold it into the declaration or to reach for a "
            "blanket reset that destroys the evidence the final report depends on.",
        ],
        "how_it_works": [
            "The spacecraft, orbit, ground network and tasking areas match Module 9, so crews are "
            "not learning a new environment while under pressure. What changes is what is running "
            "and what the crew is expected to do about it.",
            "Navigation interference and a telemetry text inject are present again. This time a "
            "reaction wheel is jammed from the moment the session starts and does not clear on "
            "its own, so the crew has to diagnose and recover it while working the incident. "
            "Products captured while the position solution was untrustworthy have to be held "
            "rather than released.",
            "The scored questions cover the incident scope, the rollback step that clears the "
            "tampered telemetry, which ground station to keep out of the recovery pass rotation, "
            "payload quarantine and re-baselining, and the content and cadence of a recovery "
            "report. "
            "Recovery reports are expected every fifteen simulation minutes.",
        ],
        "instructor_notes": [
            "This module rewards deliberate action, so resist prompting. A crew that resets "
            "everything at the first sign of trouble is producing exactly the outcome the module "
            "exists to expose.",
            "The wheel fault persists until the crew acts on it. If they never diagnose it, "
            "pointing stays degraded and the collection tasks suffer, which is the intended "
            "consequence.",
            "Hold crews to the fifteen minute reporting cadence. Consistency between reports "
            "matters more than polish in any one of them.",
            "Watch the scope decision closely. Folding the hardware fault into the cyber "
            "declaration is the most common error, and it is the same error Module 9 sets up.",
            "Products geotagged while navigation was interfered with are the ones at risk. Ask "
            "any crew that releases everything how it verified position.",
        ],
    },
}

TYPE_LABELS = {
    "select": "Single choice",
    "checkbox": "Multiple choice, select all that apply",
    "number": "Numeric entry",
    "text": "Free text entry",
}

XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
W_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

# Studio theme colours. WordprocessingML takes hex without the leading hash.
COLOR_PRIMARY = "8B5CF6"  # Title and Heading 1
COLOR_SECONDARY = "A78BFA"  # Heading 2
COLOR_BOX = "94A3B8"  # Box outlines and table rules
COLOR_RED = "FF3838"  # Warnings
COLOR_BOX_FILL = "F1F5F9"  # Light tint from the same family as COLOR_BOX
COLOR_MUTED = "64748B"  # Question metadata lines
COLOR_TEXT = "1E293B"  # Question titles


# --------------------------------------------------------------------------------------
# WordprocessingML helpers
# --------------------------------------------------------------------------------------


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def run(
    text: str,
    *,
    bold: bool = False,
    italic: bool = False,
    color: str | None = None,
    size_pt: float | None = None,
) -> str:
    properties = []
    if bold:
        properties.append("<w:b/>")
    if italic:
        properties.append("<w:i/>")
    if color:
        properties.append(f'<w:color w:val="{color}"/>')
    if size_pt:
        half_points = int(size_pt * 2)
        properties.append(f'<w:sz w:val="{half_points}"/><w:szCs w:val="{half_points}"/>')
    run_properties = f"<w:rPr>{''.join(properties)}</w:rPr>" if properties else ""
    return f'<w:r>{run_properties}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def paragraph(
    runs: list[str] | str,
    *,
    style: str | None = None,
    bullet: bool = False,
    boxed: bool = False,
    shading: str | None = None,
    space_before: int | None = None,
    space_after: int | None = None,
) -> str:
    """Build a paragraph. Property order follows the WordprocessingML schema sequence."""
    if isinstance(runs, str):
        runs = [run(runs)]

    properties = []
    if style:
        properties.append(f'<w:pStyle w:val="{style}"/>')
    if bullet:
        properties.append('<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>')
    if boxed:
        edges = "".join(
            f'<w:{edge} w:val="single" w:sz="4" w:space="6" w:color="{COLOR_BOX}"/>'
            for edge in ("top", "left", "bottom", "right")
        )
        properties.append(f"<w:pBdr>{edges}</w:pBdr>")
    if shading:
        properties.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{shading}"/>')
    if space_before is not None or space_after is not None:
        spacing = []
        if space_before is not None:
            spacing.append(f'w:before="{space_before}"')
        if space_after is not None:
            spacing.append(f'w:after="{space_after}"')
        properties.append(f"<w:spacing {' '.join(spacing)}/>")

    paragraph_properties = f"<w:pPr>{''.join(properties)}</w:pPr>" if properties else ""
    return f"<w:p>{paragraph_properties}{''.join(runs)}</w:p>"


def heading(text: str, level: int) -> str:
    style = "Title" if level == 0 else f"Heading{level}"
    return paragraph(text, style=style)


def question_heading(text: str, *, first_in_section: bool = False) -> str:
    """Question headings sit in a shaded box so each question reads as its own block.

    The first question in a stream sits tight under its stream heading so the two read as
    a group, rather than the question competing with the stream heading for attention.
    """
    return paragraph(
        text,
        style="Heading3",
        boxed=True,
        shading=COLOR_BOX_FILL,
        space_before=80 if first_in_section else 360,
        space_after=140,
    )


def labelled(label: str, value: str) -> str:
    return paragraph([run(f"{label} ", bold=True), run(value)])


def bullet(text: str, *, bold: bool = False) -> str:
    return paragraph([run(text, bold=bold)], style="ListParagraph", bullet=True)


def table(rows: list[tuple[str, str]]) -> str:
    borders = "".join(
        f'<w:{edge} w:val="single" w:sz="4" w:space="0" w:color="{COLOR_BOX}"/>'
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV")
    )
    cell_margins = (
        "<w:tblCellMar>"
        '<w:top w:w="60" w:type="dxa"/><w:left w:w="108" w:type="dxa"/>'
        '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="108" w:type="dxa"/>'
        "</w:tblCellMar>"
    )
    properties = (
        "<w:tblPr>"
        '<w:tblW w:w="5000" w:type="pct"/>'
        f"<w:tblBorders>{borders}</w:tblBorders>"
        f"{cell_margins}"
        "</w:tblPr>"
    )
    grid = '<w:tblGrid><w:gridCol w:w="2600"/><w:gridCol w:w="7000"/></w:tblGrid>'

    body = []
    for label, value in rows:
        label_cell = (
            f'<w:tc><w:tcPr><w:tcW w:w="27" w:type="pct"/></w:tcPr>'
            f"{paragraph([run(label, bold=True)])}</w:tc>"
        )
        value_cell = (
            f'<w:tc><w:tcPr><w:tcW w:w="73" w:type="pct"/></w:tcPr>'
            f"{paragraph(value)}</w:tc>"
        )
        body.append(f"<w:tr>{label_cell}{value_cell}</w:tr>")

    return f"<w:tbl>{properties}{grid}{''.join(body)}</w:tbl>{paragraph('')}"


def styles_xml() -> str:
    def style(
        style_id: str,
        name: str,
        *,
        size_pt: float | None = None,
        bold: bool = False,
        color: str | None = None,
        before: int = 0,
        after: int = 160,
        keep_next: bool = False,
        indent_left: int | None = None,
        outline_level: int | None = None,
        border_bottom: str | None = None,
    ) -> str:
        paragraph_properties = []
        if keep_next:
            paragraph_properties.append("<w:keepNext/><w:keepLines/>")
        if border_bottom:
            paragraph_properties.append(
                "<w:pBdr>"
                f'<w:bottom w:val="single" w:sz="8" w:space="3" w:color="{border_bottom}"/>'
                "</w:pBdr>"
            )
        paragraph_properties.append(f'<w:spacing w:before="{before}" w:after="{after}"/>')
        if indent_left is not None:
            paragraph_properties.append(f'<w:ind w:left="{indent_left}"/>')
            paragraph_properties.append("<w:contextualSpacing/>")
        if outline_level is not None:
            paragraph_properties.append(f'<w:outlineLvl w:val="{outline_level}"/>')

        run_properties = []
        if bold:
            run_properties.append("<w:b/>")
        if color:
            run_properties.append(f'<w:color w:val="{color}"/>')
        if size_pt:
            half_points = int(size_pt * 2)
            run_properties.append(
                f'<w:sz w:val="{half_points}"/><w:szCs w:val="{half_points}"/>'
            )

        return (
            f'<w:style w:type="paragraph" w:styleId="{style_id}">'
            f'<w:name w:val="{name}"/>'
            '<w:basedOn w:val="Normal"/><w:qFormat/>'
            f"<w:pPr>{''.join(paragraph_properties)}</w:pPr>"
            f"<w:rPr>{''.join(run_properties)}</w:rPr>"
            "</w:style>"
        )

    document_defaults = (
        "<w:docDefaults><w:rPrDefault><w:rPr>"
        '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>'
        '<w:sz w:val="22"/><w:szCs w:val="22"/>'
        "</w:rPr></w:rPrDefault>"
        "<w:pPrDefault><w:pPr>"
        '<w:spacing w:after="160" w:line="264" w:lineRule="auto"/>'
        "</w:pPr></w:pPrDefault></w:docDefaults>"
    )

    normal = (
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
        '<w:name w:val="Normal"/><w:qFormat/></w:style>'
    )

    return (
        XML_DECLARATION
        + f"<w:styles {W_NS}>"
        + document_defaults
        + normal
        + style("Title", "Title", size_pt=26, bold=True, color=COLOR_PRIMARY, after=80)
        + style(
            "Heading1",
            "heading 1",
            size_pt=16,
            bold=True,
            color=COLOR_PRIMARY,
            before=360,
            after=120,
            keep_next=True,
            outline_level=0,
        )
        + style(
            "Heading2",
            "heading 2",
            size_pt=14.5,
            bold=True,
            color=COLOR_SECONDARY,
            before=440,
            after=60,
            keep_next=True,
            outline_level=1,
            border_bottom=COLOR_SECONDARY,
        )
        + style(
            "Heading3",
            "heading 3",
            size_pt=11,
            bold=True,
            color=COLOR_TEXT,
            before=220,
            after=60,
            keep_next=True,
            outline_level=2,
        )
        + style("ListParagraph", "List Paragraph", after=60, indent_left=720)
        + "</w:styles>"
    )


def numbering_xml() -> str:
    return (
        XML_DECLARATION
        + f"<w:numbering {W_NS}>"
        + '<w:abstractNum w:abstractNumId="0">'
        + '<w:multiLevelType w:val="hybridMultilevel"/>'
        + '<w:lvl w:ilvl="0">'
        + '<w:start w:val="1"/><w:numFmt w:val="bullet"/>'
        + '<w:lvlText w:val="&#xF0B7;"/><w:lvlJc w:val="left"/>'
        + '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
        + '<w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol" w:hint="default"/></w:rPr>'
        + "</w:lvl></w:abstractNum>"
        + '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
        + "</w:numbering>"
    )


def document_xml(body: list[str]) -> str:
    section = (
        "<w:sectPr>"
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"'
        ' w:header="709" w:footer="709" w:gutter="0"/>'
        "</w:sectPr>"
    )
    return (
        XML_DECLARATION
        + f"<w:document {W_NS}><w:body>{''.join(body)}{section}</w:body></w:document>"
    )


def core_properties_xml(title: str, description: str) -> str:
    return (
        XML_DECLARATION
        + "<cp:coreProperties"
        ' xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"'
        ' xmlns:dc="http://purl.org/dc/elements/1.1/">'
        f"<dc:title>{escape(title)}</dc:title>"
        f"<dc:description>{escape(description)}</dc:description>"
        "</cp:coreProperties>"
    )


def write_docx(path: Path, body: list[str], title: str, description: str) -> None:
    content_types = (
        XML_DECLARATION
        + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels"'
        ' ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument'
        '.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument'
        '.wordprocessingml.styles+xml"/>'
        '<Override PartName="/word/numbering.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument'
        '.wordprocessingml.numbering+xml"/>'
        '<Override PartName="/docProps/core.xml"'
        ' ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        "</Types>"
    )

    package_rels = (
        XML_DECLARATION
        + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1"'
        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"'
        ' Target="word/document.xml"/>'
        '<Relationship Id="rId2"'
        ' Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata'
        '/core-properties" Target="docProps/core.xml"/>'
        "</Relationships>"
    )

    document_rels = (
        XML_DECLARATION
        + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1"'
        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"'
        ' Target="styles.xml"/>'
        '<Relationship Id="rId2"'
        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering"'
        ' Target="numbering.xml"/>'
        "</Relationships>"
    )

    if path.with_name(f"~${path.name[2:]}").exists():
        raise SystemExit(
            f"{path.name} is open in Word. Close it and run this script again."
        )

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", package_rels)
        archive.writestr("word/_rels/document.xml.rels", document_rels)
        archive.writestr("word/document.xml", document_xml(body))
        archive.writestr("word/styles.xml", styles_xml())
        archive.writestr("word/numbering.xml", numbering_xml())
        archive.writestr("docProps/core.xml", core_properties_xml(title, description))


# --------------------------------------------------------------------------------------
# Scenario to guide content
# --------------------------------------------------------------------------------------


def format_number(value: float) -> str:
    return f"{value:g}"


def format_correct_answer(question: dict) -> str:
    answer = question["answer"]
    question_type = question["type"]
    options = answer.get("options", [])

    if question_type == "select":
        return options[answer["value"]]

    if question_type == "checkbox":
        return ", ".join(options[index] for index in answer["value"])

    if question_type == "number":
        unit = answer.get("unit", "")
        text = format_number(answer["value"])
        if unit:
            text += f" {unit}"
        tolerance = answer.get("tolerance")
        if tolerance:
            suffix = f" {unit}" if unit else ""
            text += f" (accepted within +/- {format_number(tolerance)}{suffix})"
        else:
            text += " (exact value required)"
        return text

    if question_type == "text":
        return f'"{answer["value"]}"'

    raise ValueError(f"Unsupported question type: {question_type!r}")


def at_a_glance_rows(scenario: dict, content: dict) -> list[tuple[str, str]]:
    simulation = scenario["simulation"]
    end_time = simulation["end_time"]
    speed = simulation["speed"]

    if end_time == 0:
        session_length = "Open ended, instructor controlled"
    elif speed == 1:
        session_length = f"{format_number(end_time / 60)} minutes"
    else:
        session_length = (
            f"{format_number(end_time / 60)} simulation minutes, "
            f"about {format_number(end_time / (60 * speed))} minutes real time "
            f"at {format_number(speed)}x speed"
        )

    questions = scenario["questions"]
    streams = list(dict.fromkeys(question["section"] for question in questions))
    events = scenario.get("events", [])

    return [
        ("Theme", str(content["theme"])),
        ("Session length", session_length),
        ("Start epoch", simulation["epoch"].replace("/", "-") + " UTC"),
        ("Ground stations", ", ".join(scenario["ground_stations"]["locations"])),
        ("Scripted events", str(len(events)) if events else "None"),
        ("Question streams", ", ".join(streams)),
        (
            "Scoring",
            f"{len(questions)} questions, "
            f"{sum(question['answer']['score'] for question in questions)} points total",
        ),
    ]


def question_body(scenario: dict) -> list[str]:
    body: list[str] = []
    current_section = None

    for number, question in enumerate(scenario["questions"], start=1):
        section = question["section"]
        starts_section = section != current_section
        if starts_section:
            body.append(heading(section, 2))
            current_section = section

        answer = question["answer"]
        body.append(
            question_heading(
                f"Q{number}. {question['title']}", first_in_section=starts_section
            )
        )
        body.append(
            paragraph(
                [
                    run(
                        f"{TYPE_LABELS[question['type']]}  |  {answer['score']} points",
                        italic=True,
                        color=COLOR_MUTED,
                        size_pt=9,
                    )
                ],
                space_after=80,
            )
        )
        body.append(labelled("Shown to teams as:", question["description"]))

        options = answer.get("options")
        if options:
            correct = (
                {answer["value"]} if question["type"] == "select" else set(answer["value"])
            )
            for index, option in enumerate(options):
                is_correct = index in correct
                text = f"{option} (correct)" if is_correct else option
                body.append(bullet(text, bold=is_correct))

        body.append(labelled("Correct answer:", format_correct_answer(question)))
        body.append(labelled("Why:", answer["reason"]))

    return body


def build_guide(module: int, content: dict) -> Path:
    scenario_path = SCENARIO_DIR / f"module_{module}.json"
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))

    title = f"FSSCP Module {module} - Instructor Guide"
    body: list[str] = [heading(title, 0)]
    body.append(
        paragraph(
            [
                run(
                    "Instructor copy. This document contains the scored answers and must not "
                    "be shared with participating teams.",
                    bold=True,
                    color=COLOR_RED,
                )
            ]
        )
    )

    body.append(heading("At a Glance", 1))
    body.append(table(at_a_glance_rows(scenario, content)))

    body.append(heading("Purpose", 1))
    body.extend(paragraph(text) for text in content["purpose"])

    body.append(heading("How the Module Works", 1))
    body.extend(paragraph(text) for text in content["how_it_works"])

    body.append(heading("Running the Module", 1))
    body.extend(bullet(text) for text in content["instructor_notes"])

    body.append(heading("Questions and Answers", 1))
    body.append(
        paragraph(
            "Questions are delivered in the Tasks section of the operator terminal. Teams may "
            "submit once per question, after which the question locks."
        )
    )
    body.extend(question_body(scenario))

    output_path = SCENARIO_DIR / f"module_{module}_instructor_guide.docx"
    write_docx(
        output_path,
        body,
        title,
        "Instructor copy. Contains scored answers. Not for participant distribution.",
    )
    return output_path


def main() -> None:
    for module, content in sorted(MODULE_CONTENT.items()):
        output_path = build_guide(module, content)
        print(f"Wrote {output_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()

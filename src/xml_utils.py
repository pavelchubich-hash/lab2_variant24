"""XML serialization and parsing helpers for HTTP API."""

import xml.etree.ElementTree as ET

STATUS_OK = "ok"
EMPTY_LENGTH = 0
DEFAULT_OFFSET = 0


def create_element_with_text(tag: str, text_val: str) -> ET.Element:
    """Create an XML element with inner text."""
    elem = ET.Element(tag)
    elem.text = str(text_val)
    return elem


def serialize_id_response(identifier: int) -> str:
    """Serialize single identifier response to XML string."""
    root = ET.Element("response", {"status": STATUS_OK})
    root.append(create_element_with_text("identifier", str(identifier)))
    return ET.tostring(root, encoding="utf-8").decode("utf-8")


def serialize_status_response(success: bool) -> str:
    """Serialize boolean operation status to XML string."""
    root = ET.Element("response", {"status": STATUS_OK})
    val = "true" if success else "false"
    root.append(create_element_with_text("success", val))
    return ET.tostring(root, encoding="utf-8").decode("utf-8")


def serialize_error(code: int, message: str) -> str:
    """Serialize error status and message to XML string."""
    root = ET.Element("error")
    root.append(create_element_with_text("code", str(code)))
    root.append(create_element_with_text("message", message))
    return ET.tostring(root, encoding="utf-8").decode("utf-8")


def _append_person_node(parent: ET.Element, item: tuple) -> None:
    """Append person entity sub elements to parent XML node."""
    node = ET.SubElement(parent, "person")
    node.append(create_element_with_text("identifier", str(item[0])))
    node.append(create_element_with_text("created", str(item[1])))
    node.append(create_element_with_text("ip", item[2]))
    node.append(create_element_with_text("platform", item[3]))
    node.append(create_element_with_text("user_agent", item[4]))


def serialize_persons(persons: list) -> str:
    """Serialize list of persons to XML string."""
    root = ET.Element("persons")
    for item in persons:
        _append_person_node(root, item)
    return ET.tostring(root, encoding="utf-8").decode("utf-8")


def _append_command_node(parent: ET.Element, item: tuple) -> None:
    """Append command entity sub elements to parent XML node."""
    node = ET.SubElement(parent, "command")
    node.append(create_element_with_text("identifier", str(item[0])))
    node.append(create_element_with_text("created", str(item[1])))
    node.append(create_element_with_text("data", item[2]))
    node.append(create_element_with_text("person", str(item[3])))
    node.append(create_element_with_text("tags", item[4]))
    node.append(create_element_with_text("status", item[5]))
    node.append(create_element_with_text("triggered", str(item[6])))


def serialize_commands(commands: list) -> str:
    """Serialize list of commands to XML string."""
    root = ET.Element("commands")
    for item in commands:
        _append_command_node(root, item)
    return ET.tostring(root, encoding="utf-8").decode("utf-8")


def _append_result_node(parent: ET.Element, item: tuple) -> None:
    """Append result entity sub elements to parent XML node."""
    node = ET.SubElement(parent, "result")
    node.append(create_element_with_text("identifier", str(item[0])))
    node.append(create_element_with_text("created", str(item[1])))
    node.append(create_element_with_text("result", item[2]))
    node.append(create_element_with_text("status", item[3]))
    node.append(create_element_with_text("exception", item[4]))
    node.append(create_element_with_text("command", str(item[5])))


def serialize_results(results: list) -> str:
    """Serialize list of results to XML string."""
    root = ET.Element("results")
    for item in results:
        _append_result_node(root, item)
    return ET.tostring(root, encoding="utf-8").decode("utf-8")


def serialize_report(items: list) -> str:
    """Serialize report rows of tags and result to XML string."""
    root = ET.Element("report")
    for item in items:
        node = ET.SubElement(root, "item")
        node.append(create_element_with_text("tags", str(item[0])))
        node.append(create_element_with_text("result", str(item[1])))
    return ET.tostring(root, encoding="utf-8").decode("utf-8")


def parse_xml_to_dict(xml_text: str) -> dict:
    """Parse XML string into nested dictionary structure."""
    if len(xml_text.strip()) == EMPTY_LENGTH:
        return {}
    root = ET.fromstring(xml_text)
    data = {}
    for child in root:
        data[child.tag] = child.text
    return data


def parse_xml_items(xml_text: str, item_tag: str) -> list:
    """Parse list of entity items from XML text."""
    if len(xml_text.strip()) == EMPTY_LENGTH:
        return []
    root = ET.fromstring(xml_text)
    items = []
    for elem in root.findall(item_tag):
        row = {}
        for child in elem:
            row[child.tag] = child.text
        items.append(row)
    return items

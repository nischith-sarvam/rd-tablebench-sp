"""
For each format, this code extracts the largest HTML table from the response.
"""

import json
from typing import Any
import os
from bs4 import BeautifulSoup
import re


def parse_textract_response(path: str) -> tuple[str | None, Any]:
    if not os.path.exists(path):
        return None, None

    with open(path, "r") as f:
        data = json.load(f)

    return data["html_table"], data


def parse_gcloud_response(path: str) -> tuple[str | None, Any]:
    if not os.path.exists(path):
        return None, None

    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception:
        return None, None

    return data["html_table"], data


def parse_reducto_response(path: str) -> tuple[str | None, Any]:
    if not os.path.exists(path):
        return None, None

    with open(path, "r") as f:
        data = json.load(f)

    if "error" in data:
        return None, data

    longest_html = None
    max_length = 0

    for chunk in data["result"]["chunks"]:
        blocks = chunk["blocks"]
        for block in blocks:
            if block["type"] == "Table":
                if len(block["content"]) > max_length:
                    max_length = len(block["content"])
                    longest_html = block["content"]

    return longest_html, data


def parse_chunkr_response(path: str) -> tuple[str | None, Any]:
    if not os.path.exists(path):
        return None, None

    with open(path, "r") as f:
        data = json.load(f)

    if data.get("status") != "Succeeded":
        return None, data

    largest_html = None
    max_length = 0

    try:
        for output in (
            data.get("output", [])
            if "chunks" not in data.get("output")
            else data["output"]["chunks"]
        ):
            for segment in output.get("segments", []):
                if segment.get("segment_type") == "Table" and segment.get("html"):
                    if len(segment["html"]) > max_length:
                        max_length = len(segment["html"])
                        largest_html = segment["html"]
    except Exception:
        import traceback

        traceback.print_exc()
        print(data)

    return largest_html, data


def parse_unstructured_response(path: str) -> tuple[str | None, Any]:
    if not os.path.exists(path):
        return None, None

    with open(path, "r") as f:
        data = json.load(f)

    largest_html = None
    max_length = 0

    for element in data.get("elements", []):
        if element.get("type") == "Table" and element.get("metadata", {}).get(
            "text_as_html"
        ):
            html = element["metadata"]["text_as_html"]
            if len(html) > max_length:
                max_length = len(html)
                largest_html = html

    return largest_html, data


def parse_gpt4o_response(path: str) -> tuple[str | None, Any]:
    if not os.path.exists(path):
        return None, None

    with open(path, "r") as f:
        data = json.load(f)

    html = data["html_table"]
    # Extract just the table portion between <table> and </table>
    start = html.find("<table>")
    end = html.find("</table>") + 8
    if start != -1 and end != -1:
        return html[start:end], data
    return None, data


def parse_azure_response(path: str) -> tuple[str | None, Any]:
    data = None
    try:
        with open(path, "r") as f:
            data = json.load(f)

        def azure_to_html(table: Any) -> str:
            html = "<table>"
            for row_index in range(table["rowCount"]):
                html += "<tr>"
                for col_index in range(table["columnCount"]):
                    cell = next(
                        (
                            c
                            for c in table["cells"]
                            if c["rowIndex"] == row_index
                            and c["columnIndex"] == col_index
                        ),
                        None,
                    )
                    if cell:
                        content = (
                            cell["content"]
                            .replace(":selected:", "")
                            .replace(":unselected:", "")
                        )
                        tag = "th" if cell.get("kind") == "columnHeader" else "td"
                        rowspan = (
                            f" rowspan='{cell['rowSpan']}'" if "rowSpan" in cell else ""
                        )
                        colspan = (
                            f" colspan='{cell['columnSpan']}'"
                            if "columnSpan" in cell
                            else ""
                        )
                        html += f"<{tag}{rowspan}{colspan}>{content}</{tag}>"
                    else:
                        pass
                html += "</tr>"
            html += "</table>"
            return html

        # Find table with largest area (row count * column count)
        largest_table = max(
            data["tables"], key=lambda t: t["rowCount"] * t["columnCount"]
        )
        return azure_to_html(largest_table), data
    except Exception:
        return None, data


def extract_largest_table(html_content):
    # Parse HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all tables in the body
    tables = soup.find_all('table')
    
    if not tables:
        print("No tables found in the input file.")
        return ""
    
    # Initialize variables to track the largest table
    max_length = -1
    selected_table = None
    
    for table in tables:
        # Calculate the length of this table (excluding tags)
        current_length = len(str(table))
        
        if current_length > max_length or max_length == -1:
            max_length = current_length
            selected_table = table
    
    if selected_table is not None:
        return selected_table
    else:
        return ""


def parse_sarvam_outputs(path: str):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        html_content = ""
        with open(file_path, "r") as f:
            html_content = f.read()
        table_content = extract_largest_table(html_content)
        table_content = str(table_content)
        if table_content:
            with open(file_path, "w") as f:
                f.write(table_content)
        else:
            print(f"No table found in {file_path}")
            os.remove(file_path)

def parse_claude_outputs(inp_path:str, out_path:str): 
    for file in os.listdir(inp_path):
        if file.endswith(".json"):
            file_path = os.path.join(inp_path, file)
            (table, data) = parse_gpt4o_response(file_path)
            # store the table in the out_path as a html file
            if table:
                with open(os.path.join(out_path, file.replace(".json", ".html")), "w") as f:
                    f.write(table)
            else:
                print(f"No table found in {file_path}")
                # os.remove(file_path)

def parse_reducto_outputs(inp_path:str, out_path:str): 
    empty_files = []
    for file in os.listdir(inp_path):
        if file.endswith(".json"):
            file_path = os.path.join(inp_path, file)
            (table, data) = parse_reducto_response(file_path)
            # store the table in the out_path as a html file
            if table:
                with open(os.path.join(out_path, file.replace(".json", ".html")), "w") as f:
                    f.write(table)
            else:
                match = re.search(r"(\d+)_png", file)
                if match:
                    empty_files.append(match.group(1))
                print(f"No table found in {file_path}")
                # os.remove(file_path)
    print(empty_files)
        
# if __name__ == "__main__":
#     inp_path="/home/vansh/work/sarvam/rd-tablebench-sp/data/claude_sp"
#     # out_path="/home/vansh/work/sarvam/rd-tablebench-sp/data/providers/reducto_sp"
#     # parse_reducto_outputs(inp_path, out_path)

#     out_path="/home/vansh/work/sarvam/rd-tablebench-sp/data/providers/claude_sp"
#     parse_claude_outputs(inp_path, out_path)


parse_sarvam_outputs("../data/providers/sarvam-parse")

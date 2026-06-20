import os
import pdfplumber
from datetime import datetime
from crewai.tools import tool
from config import REPORTS_DIR

@tool("FileReaderTool")
def file_reader_tool(file_path: str) -> str:
    """
    Reads the content of a given file path. 
    Supports .txt and .pdf files. 
    Returns the text content of the file.
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"
        
        # Handle PDF files
        if file_path.lower().endswith(".pdf"):
            text_content = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
            return text_content.strip()
            
        # Handle TXT and other default files
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"


@tool("ReportSaverTool")
def report_saver_tool(filename: str, job_id: str, content: str) -> str:
    """
    Saves a Markdown report to the filesystem.
    Args:
        filename: Base name for the file, e.g. '01_gap_analysis' (no extension needed)
        job_id: The unique job identifier string
        content: The full Markdown content to write into the report file
    Returns:
        A success or error message string.
    """
    try:
        if not all([filename, job_id, content]):
            return "Error: 'filename', 'job_id', and 'content' are all required."

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_content = f"<!-- Report Generated At: {timestamp} -->\n\n{content}"

        # Strip .md extension if accidentally included
        if filename.endswith(".md"):
            filename = filename[:-3]

        file_name = f"{job_id}_{filename}.md"
        save_path = os.path.join(REPORTS_DIR, file_name)

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        return f"Successfully saved report to {save_path}"

    except Exception as e:
        return f"Error saving report: {str(e)}"
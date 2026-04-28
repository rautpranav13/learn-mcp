from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("DocumentMCP", log_level="ERROR")

# -------------------------------
# In-memory document store
# -------------------------------
docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}


# =========================================================
# 🛠 TOOLS
# =========================================================

@mcp.tool(
    name="read_document",
    description="Read the contents of a document and return as string."
)
def read_document(
    doc_id: str = Field(description="Document ID to read")
):
    if doc_id not in docs:
        raise ValueError(f"Document with Doc ID {doc_id} not found")

    return docs[doc_id]


@mcp.tool(
    name="edit_document",
    description="Replace text in a document with new text."
)
def edit_document(
    doc_id: str = Field(description="Document ID"),
    old_strng: str = Field(description="Exact text to replace"),
    new_strng: str = Field(description="New text")
):
    if doc_id not in docs:
        raise ValueError(f"Document with Doc ID {doc_id} not found")

    docs[doc_id] = docs[doc_id].replace(old_strng, new_strng)
    return f"Document {doc_id} updated successfully."


# =========================================================
# 📦 RESOURCES
# =========================================================

@mcp.resource("docs://documents")
def list_documents():
    """
    Returns list of available document IDs
    """
    return list(docs.keys())


@mcp.resource("docs://documents/{doc_id}")
def get_document(doc_id: str):
    """
    Returns content of a specific document
    """
    if doc_id not in docs:
        raise ValueError(f"Document with Doc ID {doc_id} not found")

    return docs[doc_id]


# =========================================================
# 🧠 PROMPTS (for CLI slash commands)
# =========================================================

@mcp.prompt(
    name="summarize",
    description="Summarize a document",
)
def summarize_prompt(doc_id: str):
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id} not found")

    return [
        {
            "role": "user",
            "content": f"Summarize the following document:\n\n{docs[doc_id]}"
        }
    ]


@mcp.prompt(
    name="rewrite_markdown",
    description="Rewrite a document in clean markdown format",
)
def rewrite_markdown_prompt(doc_id: str):
    if doc_id not in docs:
        raise ValueError(f"Document {doc_id} not found")

    return [
        {
            "role": "user",
            "content": f"Rewrite this into well-structured markdown:\n\n{docs[doc_id]}"
        }
    ]


# =========================================================
# 🚀 RUN SERVER
# =========================================================

if __name__ == "__main__":
    mcp.run(transport="stdio")
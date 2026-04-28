What I did:

# Project Setup
1. created a workspace skilljar_mcp in VS Code
2. downloaded, extracted in the workspace:
    cli_project.zip from https://anthropic.skilljar.com/introduction-to-model-context-protocol/296694

3. install uv using homebrew:
    brew install uv

4. created and activated venv
    uv venv
    source .venv/bin/activate 

5. installed dependencies:
    uv pip install -e

6. created anthropic api key:
    https://platform.claude.com/settings/workspaces/default/keys

7. pasted in the .env

# Adding tools (MCP Server), mcp_server.py
8. added mcp tool to read document:
    # tool to read a doc
@mcp.tool(
    name="read_document",
    description="Read the contents of the document and returns as a string."
)
def read_document(
    doc_id: str = Field(description="Doc ID of the document to read")
):
    if doc_id not in docs:
        raise ValueError(f"Document with Doc ID {doc_id} not found")
    
    return docs[doc_id]

9. added mcp tool to edit document
# tool to edit a doc
@mcp.tool(
    name="edit_document",
    description="Edit the contents of a Document by replacing a string in the documents content with a new string."
)
def edit_document(
    doc_id: str = Field(description="Doc ID of the document to edited"),
    old_strng: str = Field(description="The text to replace. Must match exactly, including whitespaces."),
    new_strng: str = Field(description="The new text to insert in place of the old text.")
):
    if doc_id not in docs:
        raise ValueError(f"Document with Doc ID {doc_id} not found")
    
    docs[doc_id] = docs[doc_id].replace(old_strng, new_strng)

# Run and inspect the project

10. run the project:
    uv run main.py

11. open mcp server inspector:
    make sure we are inside python venv
    source .venv/bin/activate

    and then:
    mcp dev mcp_server.py

    browser is opened.

12. click "Connect" to establish connection with the local mcp running server

13. click "Tools" and then "List Tools":
    it provides the read_document and edit_document tools (we defined in the mcp_server.py)

14. click "read_document" and provide one of the documents id, here "spec.txt":
    it will show:
    Tool result: Success
    "These specifications define the technical requirements for the equipment."

    trying with some random document id, something.xyz
    Tools result: Error
    Error executing tool read_document: Document with Doc ID something.xyz not found

15. click "edit_document" and provide
    doc_id = deposition.md, old_strng = This //must be case sensitive, new_strng = A report
    this will show:
    Tool result: Success

16. Again, read_document with doc_id = "deposition.md"
    this will show:
    Tool result: Success
    A report deposition covers the testimony of Angela Smith, P.E.

# MCP Client, mcp_client.py
17. Defined function body list_tools, which will get access to the session(actual connection to the MCP server) ie. self.session() and call built in function list_tools():
    result = await self.session().list_tools()
    return result.tools

18. Defined function body call_tool, which will get access to the session(actual connection to the MCP server) ie. self.session() and call built in function call_tool with parameters tool_name: str and tool_input: dict
    return await self.session().call_tool(tool_name, tool_input)

19. Added testing lines inside main():
    result = await _client.list_tools()
    print(result)

20. run the client:
    uv run mcp_client.py
    Output:
    [Tool(name='read_document', title=None, description='Read the contents of the document and returns as a string.', inputSchema={'properties': {'doc_id': {'description': 'Doc ID of the document to read', 'title': 'Doc Id', 'type': 'string'}}, 'required': ['doc_id'], 'title': 'read_documentArguments', 'type': 'object'}, outputSchema=None, icons=None, annotations=None, meta=None, execution=None), Tool(name='edit_document', title=None, description='Edit the contents of a Document by replacing a string in the documents content with a new string.', inputSchema={'properties': {'doc_id': {'description': 'Doc ID of the document to edited', 'title': 'Doc Id', 'type': 'string'}, 'old_strng': {'description': 'The text to replace. Must match exactly, including whitespaces.', 'title': 'Old Strng', 'type': 'string'}, 'new_strng': {'description': 'The new text to insert in place of the old text.', 'title': 'New Strng', 'type': 'string'}}, 'required': ['doc_id', 'old_strng', 'new_strng'], 'title': 'edit_documentArguments', 'type': 'object'}, outputSchema=None, icons=None, annotations=None, meta=None, execution=None)]

# Ask claude.

21. run the project:
    uv run main.py

22. Ask: What is the contents of the plan.md document?
Error: anthropic.BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}, 'request_id': 'req_011CaWJUXRT4MkEX5xU4QFWd'}

Need to purchase credits. But I won't.

# Connect the same MCP to gemma4 locally.

23. Install ollama
    https://ollama.com/download

24. download gemma4:
    ollama run gemma4


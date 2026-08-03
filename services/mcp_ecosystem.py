import json
import logging

logger = logging.getLogger("MCPEcosystem")

class MCPEcosystemService:
    def __init__(self, matcher=None, calculator=None, recommender=None, rag=None):
        self.matcher = matcher
        self.calculator = calculator
        self.recommender = recommender
        self.rag = rag

    def list_tools(self):
        """
        Model Context Protocol (MCP) Tool Declarations.
        """
        return [
            {
                "name": "lookup_emission_factor",
                "description": "Find appropriate carbon emission factors using contrastive semantic search.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Description of activity or material"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "calculate_scope_3",
                "description": "Compute Scope 3 Category 1 emissions for supply chain materials.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "material": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit": {"type": "string"}
                    },
                    "required": ["material", "quantity", "unit"]
                }
            },
            {
                "name": "query_rag_assistant",
                "description": "Search compliance standards, DEFRA, EPA, and SRS documents.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "tenant_id": {"type": "string"}
                    },
                    "required": ["query", "tenant_id"]
                }
            }
        ]

    def call_tool(self, name, arguments):
        """
        Executes registered MCP tools and returns standard JSON-RPC payloads.
        """
        logger.info(f"MCP Call received: {name} with args: {arguments}")
        try:
            if name == "lookup_emission_factor":
                q = arguments.get("query")
                if self.matcher:
                    res = self.matcher.match_emission_factor(q, top_n=2)
                    return {"content": [{"type": "text", "text": json.dumps(res)}]}
                return {"content": [{"type": "text", "text": "Matcher service offline"}]}
                
            elif name == "calculate_scope_3":
                mat = arguments.get("material")
                qty = arguments.get("quantity")
                unit = arguments.get("unit")
                if self.calculator:
                    res = self.calculator.calculate_scope_3_category_1(mat, qty, unit)
                    return {"content": [{"type": "text", "text": json.dumps(res)}]}
                return {"content": [{"type": "text", "text": "Calculation engine offline"}]}
                
            elif name == "query_rag_assistant":
                q = arguments.get("query")
                tenant = arguments.get("tenant_id")
                if self.rag:
                    res = self.rag.query(q, tenant)
                    return {"content": [{"type": "text", "text": json.dumps(res)}]}
                return {"content": [{"type": "text", "text": "RAG service offline"}]}
                
            else:
                return {"isError": True, "message": f"Tool '{name}' not found in MCP registry"}
        except Exception as e:
            return {"isError": True, "message": f"MCP execution error: {str(e)}"}

if __name__ == "__main__":
    mcp = MCPEcosystemService()
    tools = mcp.list_tools()
    print("Registered MCP Tools:")
    print(json.dumps(tools, indent=2))

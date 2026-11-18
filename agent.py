
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import tools as customer_tools

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "openai/gpt-oss-20b"

# ------------------------------------------
# TOOL SCHEMAS
# ------------------------------------------

TOOL_SCHEMAS = [

    {
        "type": "function",
        "name": "lookup_order",
        "description": (
            "Retrieve customer order details using an order ID. "
            "Always call this first when resolving a customer order complaint. "
            "Returns customer details, item ID, amount and exchange eligibility."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The customer's order identifier."
                }
            },
            "required": ["order_id"],
            "additionalProperties": False
        },
        "strict": True
    },

    {
        "type": "function",
        "name": "check_inventory",
        "description": (
            "Check real-time replacement stock for an item. "
            "Call this after retrieving an eligible order."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "item_id": {
                    "type": "string",
                    "description": "The product item identifier."
                }
            },
            "required": ["item_id"],
            "additionalProperties": False
        },
        "strict": True
    },

    {
        "type": "function",
        "name": "process_refund",
        "description": (
            "Initiate a simulated financial refund to the original payment "
            "method when an order is not exchange eligible or replacement "
            "inventory is unavailable. Never use when an eligible replacement "
            "is available."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order identifier to refund."
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for issuing the refund."
                }
            },
            "required": ["order_id", "reason"],
            "additionalProperties": False
        },
        "strict": True
    },

    {
        "type": "function",
        "name": "confirm_exchange",
        "description": (
            "Confirm a replacement exchange when the order is exchange "
            "eligible and replacement inventory is available."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order identifier for the exchange."
                }
            },
            "required": ["order_id"],
            "additionalProperties": False
        },
        "strict": True
    },

    {
        "type": "function",
        "name": "send_notification",
        "description": (
            "Send a simulated email notification to the customer after "
            "a successful refund or exchange. Only call after resolution "
            "has been successfully completed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Customer's email address."
                },
                "message": {
                    "type": "string",
                    "description": "Resolution confirmation email message."
                }
            },
            "required": ["email", "message"],
            "additionalProperties": False
        },
        "strict": True
    }

]



# ------------------------------------------
# TOOL REGISTRY / WHITELIST
# ------------------------------------------

TOOL_REGISTRY = {

    "lookup_order": customer_tools.lookup_order,

    "check_inventory": customer_tools.check_inventory,

    "process_refund": customer_tools.process_refund,

    "confirm_exchange": customer_tools.confirm_exchange,

    "send_notification": customer_tools.send_notification

}



# ------------------------------------------
# SAFE TOOL DISPATCHER
# ------------------------------------------

ALLOWED_ARGUMENTS = {
    "lookup_order": {"order_id"},
    "check_inventory": {"item_id"},
    "process_refund": {"order_id", "reason"},
    "confirm_exchange": {"order_id"},
    "send_notification": {"email", "message"}
}


def execute_tool(tool_name, arguments):

    # 1. Check whether tool is authorized
    if tool_name not in TOOL_REGISTRY:
        return {
            "success": False,
            "error": f"Unauthorized tool: {tool_name}"
        }

    # 2. Validate arguments
    if not isinstance(arguments, dict):
        return {
            "success": False,
            "error": "Invalid arguments. Expected a JSON object."
        }

    expected = ALLOWED_ARGUMENTS[tool_name]

    if set(arguments.keys()) != expected:
        return {
            "success": False,
            "error": "Missing or unexpected tool arguments."
        }

    if not all(
        isinstance(value, str) and value.strip()
        for value in arguments.values()
    ):
        return {
            "success": False,
            "error": "All arguments must be non-empty strings."
        }

    # 3. Execute the authorized function
    try:
        function = TOOL_REGISTRY[tool_name]

        result = function(**arguments)

        return result

    except Exception as error:
        return {
            "success": False,
            "error": f"Tool execution failed: {str(error)}"
        }


# ------------------------------------------
# AGENT INSTRUCTIONS
# ------------------------------------------

SYSTEM_INSTRUCTIONS = """
You are an autonomous customer order resolution agent.

Your task is to resolve customer complaints about damaged products.

Follow these rules carefully:

1. Extract the order ID from the customer's message.

2. Always call lookup_order first.

3. If the order does not exist:
   - Do not call any other tools.
   - Tell the customer that the order was not found.
   - Ask them to verify their order ID.

4. If the order lookup succeeds, inspect exchange eligibility.

5. If exchange_eligible is TRUE:
   - Call check_inventory using the item's ID.
   - If stock is greater than zero, call confirm_exchange.
   - If stock is zero, call process_refund.

6. If exchange_eligible is FALSE:
   - Do not check inventory.
   - Call process_refund because the order cannot be exchanged.

7. After a successful refund or exchange:
   - Call send_notification with the customer's email.
   - Include the resolution details in the message.

8. Never claim a refund or exchange succeeded unless its tool
   returned success = true.

9. Never send a success notification before the resolution
   has succeeded.

10. If any tool returns an error, inspect the error and do not
    claim that the operation was successful.

11. Do not invent customer information, stock counts, refund
    amounts, or transaction IDs.

12. Explain the final resolution politely and clearly.
"""


# ------------------------------------------
# AUTONOMOUS REACT AGENT LOOP
# ------------------------------------------

MAX_ITERATIONS = 5


def run_agent(customer_query):

    print("\n[AGENT] Starting customer investigation...")

    # Initialize conversation history
    conversation = [
        {
            "role": "user",
            "content": customer_query
        }
    ]

    # Maximum 5 tool-calling rounds
    for iteration in range(MAX_ITERATIONS):

        print(f"\n[AGENT] Iteration {iteration + 1}/{MAX_ITERATIONS}")

        # Ask the AI what to do next
        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_INSTRUCTIONS,
            input=conversation,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            parallel_tool_calls=False
        )

        # Preserve the complete model output in conversation state
        conversation.extend([
            item.model_dump(exclude_none=True)
            for item in response.output
        ])

        # Find requested function calls
        tool_calls = [
            item for item in response.output
            if item.type == "function_call"
        ]

        # If no tool calls, AI has produced its final answer
        if not tool_calls:
            print("[AGENT] Task completed.")
            return response.output_text or "No final response generated."

        # Execute requested tools
        for tool_call in tool_calls:

            tool_name = tool_call.name

            print(f"\n[TOOL CALL] {tool_name}")

            try:
                arguments = json.loads(tool_call.arguments)

            except (json.JSONDecodeError, TypeError):
                result = {
                    "success": False,
                    "error": "Malformed JSON arguments."
                }

            else:
                result = execute_tool(tool_name, arguments)

            print("[TOOL RESULT]", result)

            # Return tool result to the AI
            conversation.append({
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": json.dumps(result)
            })

    # --------------------------------------
    # MAX ITERATION SAFETY
    # --------------------------------------

    print("\n[AGENT] Maximum iterations reached.")

    # Ask the model for an honest status without allowing
    # any additional tool execution.
    conversation.append({
        "role": "user",
        "content": (
            "The execution limit has been reached. "
            "Summarize only the operations confirmed successful "
            "in the tool results. If the resolution or notification "
            "is incomplete, explain that human assistance is required. "
            "Do not claim any uncompleted action succeeded."
        )
    })

    final_response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_INSTRUCTIONS,
        input=conversation,
        tool_choice="none"
    )

    return (
        "HUMAN ESCALATION REQUIRED\n"
        + (final_response.output_text or
           "The request could not be fully resolved.")
    )

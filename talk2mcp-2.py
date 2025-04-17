import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
email_address = os.getenv("EMAIL_ADDRESS")

max_iterations = 7
last_response = None
iteration = 0
iteration_response = []

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to Math MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["example2-3.py"]
        )

        print("Establishing connection to GmailMCP server...")
        gmail_server_params = StdioServerParameters(
            command="python",
            args=["server.py"]
        )

        async with stdio_client(server_params) as (read, write):
            async with stdio_client(gmail_server_params) as (gmail_read, gmail_write):
                print("Connection established, creating session...")
                async with ClientSession(read, write) as session:
                    async with ClientSession(gmail_read, gmail_write) as gmail_session:
                        print("Session created, initializing...")
                        await session.initialize()
                        await gmail_session.initialize()
                        
                        # Get available tools
                        print("Requesting tool list...")
                        tools_result = await session.list_tools()
                        gmail_tools_result = await gmail_session.list_tools()
                        tools = tools_result.tools
                        gmail_tools = gmail_tools_result.tools
                        print(f"Successfully retrieved {len(tools)} tools")
                        print(f"Successfully retrieved {len(gmail_tools)} gmail tools")

                        all_tools = tools + gmail_tools
                        #print(f"All tools: {all_tools}")
                        # Create system prompt with available tools
                        print("Creating system prompt...")
                        print(f"Number of tools: {len(all_tools)}")
                        
                        try:
                            
                            tools_description = []
                            for i, tool in enumerate(all_tools):
                                try:
                                    # Get tool properties
                                    params = tool.inputSchema
                                    desc = getattr(tool, 'description', 'No description available')
                                    name = getattr(tool, 'name', f'tool_{i}')
                                    
                                    # Format the input schema in a more readable way
                                    if 'properties' in params:
                                        param_details = []
                                        for param_name, param_info in params['properties'].items():
                                            param_type = param_info.get('type', 'unknown')
                                            param_details.append(f"{param_name}: {param_type}")
                                        params_str = ', '.join(param_details)
                                    else:
                                        params_str = 'no parameters'

                                    tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                                    tools_description.append(tool_desc)
                                    print(f"Added description for tool: {tool_desc}")
                                except Exception as e:
                                    print(f"Error processing tool {i}: {e}")
                                    tools_description.append(f"{i+1}. Error processing tool")
                            
                            tools_description = "\n".join(tools_description)
                            print("Successfully created tools description")
                        except Exception as e:
                            print(f"Error creating tools description: {e}")
                            tools_description = "Error loading tools"
                        
                        print("Created system prompt...")
                        
                        system_prompt = f"""You are a maths agent solving problems, capable of using gmail to send emails, in iterations. You have access to various mathematical and gmail related tools.

                        Available tools:
                        {tools_description}

                        You must respond with EXACTLY ONE line in one of these formats (no additional text):
                        1. For function calls:
                        FUNCTION_CALL: function_name|param1|param2|...
                        
                        2. For final answers:
                        FINAL_ANSWER: [number]

                        Important:
                        - When a function returns multiple values, you need to process all of them
                        - Only give FINAL_ANSWER when you have completed all necessary calculations
                        - Do not repeat function calls with the same parameters

                        Examples:
                        - FUNCTION_CALL: add|5|3
                        - FUNCTION_CALL: strings_to_chars_to_int|INDIA
                        - FINAL_ANSWER: [42]

                        DO NOT include any explanations or additional text.
                        Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:"""

                        query = f"""Find the ASCII values of characters in INDIA, calculate the sum of exponentials of those values, and send the result as an email using to {email_address}. """
                        print("Starting iteration loop...")
                        
                        # Use global iteration variables
                        global iteration, last_response
                        
                        while iteration < max_iterations:
                            print(f"\n--- Iteration {iteration + 1} ---")
                            if last_response is None:
                                current_query = query
                            else:
                                current_query = current_query + "\n\n" + " ".join(iteration_response)
                                current_query = current_query + "  What should I do next?"

                            # Get model's response with timeout
                            print("Preparing to generate LLM response...")
                            prompt = f"{system_prompt}\n\nQuery: {current_query}"
                            try:
                                response = await generate_with_timeout(client, prompt)
                                response_text = response.text.strip()
                                print(f"LLM Response: {response_text}")
                                
                                # Find the FUNCTION_CALL line in the response
                                for line in response_text.split('\n'):
                                    line = line.strip()
                                    if line.startswith("FUNCTION_CALL:"):
                                        response_text = line
                                        break
                                
                            except Exception as e:
                                print(f"Failed to get LLM response: {e}")
                                break


                            if response_text.startswith("FUNCTION_CALL:"):
                                _, function_info = response_text.split(":", 1)
                                parts = [p.strip() for p in function_info.split("|")]
                                func_name, params = parts[0], parts[1:]
                                
                                # print(f"\nDEBUG: Raw function info: {function_info}")
                                # print(f"DEBUG: Split parts: {parts}")
                                # print(f"DEBUG: Function name: {func_name}")
                                # print(f"DEBUG: Raw parameters: {params}")
                                
                                try:
                                    # Find the matching tool to get its input schema
                                    tool = next((t for t in all_tools if t.name == func_name), None)
                                    if not tool:
                                        #print(f"DEBUG: Available tools: {[t.name for t in all_tools]}")
                                        raise ValueError(f"Unknown tool: {func_name}")

                                    # print(f"DEBUG: Found tool: {tool.name}")
                                    # print(f"DEBUG: Tool schema: {tool.inputSchema}")

                                    # Prepare arguments according to the tool's input schema
                                    arguments = {}
                                    schema_properties = tool.inputSchema.get('properties', {})
                                    #print(f"DEBUG: Schema properties: {schema_properties}")

                                    for param_name, param_info in schema_properties.items():
                                        if not params:  # Check if we have enough parameters
                                            raise ValueError(f"Not enough parameters provided for {func_name}")
                                            
                                        value = params.pop(0)  # Get and remove the first parameter
                                        param_type = param_info.get('type', 'string')
                                        
                                        #print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                        
                                        # Convert the value to the correct type based on the schema
                                        if param_type == 'integer':
                                            arguments[param_name] = int(value)
                                        elif param_type == 'number':
                                            arguments[param_name] = float(value)
                                        elif param_type == 'array':
                                            # Handle array input
                                            if isinstance(value, str):
                                                value = value.strip('[]').split(',')
                                            arguments[param_name] = [int(x.strip()) for x in value]
                                        else:
                                            arguments[param_name] = str(value)

                                    # print(f"DEBUG: Final arguments: {arguments}")
                                    # print(f"DEBUG: Calling tool {func_name}")
                                    
                                    result = await session.call_tool(func_name, arguments=arguments)
                                    if result.isError:
                                        result = await gmail_session.call_tool(func_name, arguments=arguments)
                                    #print(f"Result error variable {result.isError}")
                                    #print(f"DEBUG: Raw result: {result}")
                                    
                                    # Get the full result content
                                    if hasattr(result, 'content'):
                                        #print(f"DEBUG: Result has content attribute")
                                        # Handle multiple content items
                                        if isinstance(result.content, list):
                                            iteration_result = [
                                                item.text if hasattr(item, 'text') else str(item)
                                                for item in result.content
                                            ]
                                        else:
                                            iteration_result = str(result.content)
                                    else:
                                        #print(f"DEBUG: Result has no content attribute")
                                        iteration_result = str(result)
                                        
                                    #print(f"DEBUG: Final iteration result: {iteration_result}")
                                    
                                    # Format the response based on result type
                                    if isinstance(iteration_result, list):
                                        result_str = f"[{', '.join(iteration_result)}]"
                                    else:
                                        result_str = str(iteration_result)
                                    
                                    iteration_response.append(
                                        f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                                        f"and the function returned {result_str}."
                                    )
                                    last_response = iteration_result

                                except Exception as e:
                                    # print(f"DEBUG: Error details: {str(e)}")
                                    # print(f"DEBUG: Error type: {type(e)}")
                                    import traceback
                                    traceback.print_exc()
                                    iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                                    break

                            elif response_text.startswith("FINAL_ANSWER:"):
                                print("\n=== Agent Execution Complete ===")

                                break

                            iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    

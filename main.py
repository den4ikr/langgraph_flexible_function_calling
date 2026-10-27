from dotenv import load_dotenv
from langgraph.graph import START, StateGraph, END, add_messages
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from typing import Annotated
from typing_extensions import TypedDict
from langchain.tools import tool
from langchain_core.messages import AIMessage

load_dotenv()

@tool
def palindrome_checker(text: str) -> str:
    """Check whether the exact text provided in the text argument is a palindrome.
    Do not add or infer any words that were not part of the text to check."""
    print('Checking palindrome...')
    cleaned = ''.join(char.lower() for char in text if char.isalnum())

    if cleaned == cleaned[::-1]:
        return f"The phrase or word {text} is a palindrome"
    else:
        return f"The phrase or word {text} is not a palindrome"

tools = [palindrome_checker]

llm = ChatOpenAI(model='gpt-4o-mini')
llm_with_tools = llm.bind_tools(tools)

class State(TypedDict):
    messages: Annotated[list, add_messages]

def should_continue(state: State):
    last_message = state['messages'][-1]

    if last_message.tool_calls:
        return 'tools'

    return END

def call_model(state: State):
    return {'messages': llm_with_tools.invoke(state['messages'])}

workflow = StateGraph(State)

tool_node = ToolNode(tools)

workflow.add_node('chatbot', call_model)
workflow.add_node('tools', tool_node)

workflow.add_edge(START, 'chatbot')
workflow.add_conditional_edges('chatbot', should_continue, ['tools', END])
workflow.add_edge('tools', 'chatbot')

agent = workflow.compile()

res = agent.invoke({'messages': [('user', 'Is level a palindrome?')]})

print(res['messages'][-1].content)


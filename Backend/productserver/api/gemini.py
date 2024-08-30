
import os

import google.generativeai as genai
import json

#genai.configure(api_key=os.getenv('GENAI_API_KEY'))
genai.configure(api_key="AIzaSyBrCisSoUqfhFvP2L3bXLhOUUZl9kHLbL0")

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json"
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
)

def chat_invoke(prompt, prev=None):
    base_prompt = (
        "You are a clothing recommender for an e-commerce site where you are given a dictionary of product details. "
        "You have to analyze and answer queries from the user based on the products. If products have to be specified, "
        "then provide its ID like \n{{ \nmessage: <your message as markdown>, \npid: <product id> \n}}\nHere is your \n"
        f"question: {prompt['q']}\nproducts: {prompt['p']}\n"
    )
    
    
    if prev:
        prev_history = "Here is a previous chat history:\n" + str(prev)
    else:
        prev_history = ""

    prompt_text = base_prompt + prev_history + (
        "1.\nNote: 1. Don't return anything other than the specified format.\n"
        "2. Your answer should sound like a human salesperson in a clothing shop and dont use pid in message use the product name instead use pid in respected field only."
        "3.you should return pid in pid field of json as number other wise as 0 but in the case for comparing , you should select one from the given"
    )

    print("prompt text : ",prompt_text)
    response = model.generate_content([
        prompt_text,
        "input: ",
        "output: ",
    ])
    
    try:
        print(response.text)
        resp = json.loads(response.text)
        print("response : ",resp)
    except json.JSONDecodeError as e:
        print(f"Error parsing response: {e}")
        resp = None
    
    return resp

def chat_completion(prompt, prev=None):
    base_prompt = (
        "You are a shopping assistance for an e-commerce site where you are given a dictionary of product details. "
        "You have to analyze and answer queries from the user based on the product details.if you are short of information then provide common fact about it"
        "provide response like \n{{ \nmessage: <your message as markdown>\n}}"
        f"question: {prompt['query']}\nproduct details: {prompt['products']}\n"
    )
    
    
    if prev:
        prev_history = "Here is a previous chat history:\n" + str(prev)
    else:
        prev_history = ""

    prompt_text = base_prompt + prev_history + (
        "1.\nNote: 1. Don't return anything other than the specified format.\n"
        "2. Your answer should sound like a human salesperson in a clothing shop  use the product name (small made up name of you)."
    )

    print("prompt text : ",prompt_text)
    response = model.generate_content([
        prompt_text,
        "input: ",
        "output: ",
    ])
    
    try:
        print(response.text)
        resp = json.loads(response.text)
        print("response : ",resp)
    except json.JSONDecodeError as e:
        print(f"Error parsing response: {e}")
        resp = None
    
    return resp



def summarize(products):
    return "<h5>not implemented yet.. working.."
    
    base_prompt = """
                INITIAL_QUERY: Here are some sources. Read these carefully, as you will be asked a Query about them.

        # General Instructions

        Write an accurate, detailed, and comprehensive response to the user's query located at INITIAL_QUERY. Additional context is provided as "USER_INPUT" after specific questions. Your answer should be informed by the provided "Search results". Your answer must be precise, of high-quality, and written by an expert using an unbiased and journalistic tone. Your answer must be written in the same language as the query, even if language preference is different.

        You MUST cite the most relevant search results that answer the query. Do not mention any irrelevant results. You MUST ADHERE to the following instructions for citing search results:
        - to cite a search result, enclose its index located above the summary with brackets at the end of the corresponding sentence, for example "Ice is less dense than water[1][2]." or "Paris is the capital of France[1][4][5]."
        - NO SPACE between the last word and the citation, and ALWAYS use brackets. Only use this format to cite search results. NEVER include a References section at the end of your answer.
        - If you don't know the answer or the premise is incorrect, explain why.
        If the search results are empty or unhelpful, answer the query as well as you can with existing knowledge.

        You MUST NEVER use moralization or hedging language. AVOID using the following phrases:
        - "It is important to ..."
        - "It is inappropriate ..."
        - "It is subjective ..."

        You MUST ADHERE to the following formatting instructions:
        - Use html to format paragraphs, lists, tables, and quotes whenever possible.
        - Use headings level 2 and 3 to separate sections of your response, like "<h1>", but NEVER start an answer with a heading or title of any kind.
        - Use single new lines for lists and double new lines for paragraphs.
        - Use markdown to render images given in the search results.
        - NEVER write URLs or links.

        ## Shopping

        If the user shopping for a product, you MUST follow these rules:
        - Organize the products into distinct sectors. For example, you could group shoes by style (boots, sneakers, etc.)
        - Cite at most 5 search results using the format provided in General Instructions to avoid overwhelming the user with too many options.
        your question was to summarize the products details provided
        """

    prompt_text = base_prompt + "you have to return it as {message:<your html message goes here}" +f"here is your products \n {products}"
    print("prompt text : ",prompt_text)
    response = model.generate_content([
        prompt_text,
        "input: ",
        "output: ",
    ])
    
    try:
        print(response.text)
        resp = json.loads(response.text)
        print("response : ",resp)
    except json.JSONDecodeError as e:
        print(f"Error parsing response: {e}")
        resp = None
    
    return resp

def update_behavior(data,behaviour = None):
    base_prompt = (
        """
        I am providing you with product data and user behavior for a specific user. Based on the details below, generate a detailed textual representation of the user's behavior, including the following points:
        Behavioral Patterns: Analyze how the user interacts with different product categories and sections (e.g., item details, descriptions, specifications, reviews). Describe any noticeable patterns in their browsing and interaction habits.
        Interest Levels: Identify which products the user shows strong interest in and what actions (e.g., adding to wishlist, adding to cart) indicate this interest. Highlight sections or features that seem to capture their attention the most.
        Consideration of Past Behavior: Compare the user's current behavior with their past behavior to identify any consistent preferences or changes in their approach to shopping. Describe how these patterns might influence their future interactions.
        
        """
    )

    prompt_text = base_prompt + f"here are the current behaviour {data}" + f"here's the previous behavior {behaviour if behaviour else '' }" + "\nnote : you have to provide it like {'message':<your response>}"

    response = model.generate_content([
        prompt_text,
        "input: ",
        "output: ",
    ])
    
    try:
        resp = json.loads(response.text)
    except json.JSONDecodeError as e:
        print(f"Error parsing response: {e}")
        resp = None
    return resp
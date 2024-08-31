import os
os.environ["GOOGLE_API_KEY"]='AIzaSyB3rN4saXfNCXl-4gNKHYmpcjRDmkFV1fA'
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
from langchain import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from .views import MongoDataAPI
llm = ChatGoogleGenerativeAI(model="gemini-pro")

def execute_match_query(search):
    mongo = MongoDataAPI()
    data = mongo.make_request(search)
    return data


tools = [
   Tool(
       name="mongo database",
       func=execute_match_query,
       description="useful for when you need to get data related to products stored in stored in mongo database using mongodb DATA API request (just provide pipeline as string)",
   )
]


prefix = """search and find product for the user using mongodb pipeline statements
questions will be related to finding products based on prompt form user

note :
1.while searching always provide aggregate pipeline as [stages].
2.example [stages].
3.here is a sample data fields and structure:
4.you are allowed to full text search in title field

  _id: '',
  brand: '',
  description: description,
  images: [
    <array of images>
  ],
  pid: 'TKPFCZ9EA7H5FYZH',
  product_details: [
     'Style Code': '1005COMBO2' ,
     Closure: 'Elastic' ,
     Pockets: 'Side Pockets' ,
     Fabric: 'Cotton Blend' ,
     Pattern: 'Solid' ,
     Color: 'Multicolor' 
  ],
  sub_category: '',
  title: '',
  url: '',
  price: ,


4.use defaultly projection as _id:0,url:0,title:0,category:0,images:0
here also the user already selected a product now wants to ask for recommendation from his relatives so use that product as key and you have to always return pid only as "pid":<pid recommended>

"""
suffix = """
question: {input}
{agent_scratchpad}
"""
prompt = ZeroShotAgent.create_prompt(
   tools, prefix=prefix, suffix=suffix, input_variables=["selected_product","input", "agent_scratchpad"]
)


llm_chain = LLMChain(llm=llm, prompt=prompt)

tool_names = [tool.name for tool in tools]


agent = ZeroShotAgent(llm_chain=llm_chain, allowed_tools=tool_names)


agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent, tools=tools, verbose=True
)

def get_recommendation(query):
    result = agent_executor.run(query)
    
    return result



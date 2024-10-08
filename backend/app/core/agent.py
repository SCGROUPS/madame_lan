import json
import inspect
import asyncio
import ast
from datetime import datetime
 
import requests
from openai import AsyncAzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryAnswerType, QueryCaptionType, QueryType, VectorizedQuery
from ..config import Config, LOGGER, async_timeit
 
PERSONA = Config.PERSONA
 
AzureOpenAIClient = AsyncAzureOpenAI(
    api_key=Config.AZURE_OPENAI_API_KEY,
    api_version=Config.AZURE_OPENAI_API_VERSION,
    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
)
 
AzureSearchClient = SearchClient(
    endpoint=Config.COGNITIVE_SEARCH_ENDPOINT,
    index_name=Config.COGNITIVE_SEARCH_INDEX_NAME,
    credential=AzureKeyCredential(Config.COGNITIVE_SEARCH_API_KEY)
)
 
class ToolResponseFormat:
    content: str
    args: dict
 
    def __init__(self, content: str, **args) -> "ToolResponseFormat":
        self.content = content
        self.args = args
 
    def get_args(self, key: str) -> any:
        return self.args.get(key)
 
def get_current_date():
    return datetime.now().strftime("%A, %B %d, %Y")
 
def get_prompt_by_search_mode():
    if Config.LOCAL_SEARCH > 0:
        # local_search
        if Config.INTERNET_SEARCH > 0:
            # AND internet_search
            prompt = "The given information is a combination of both Local Search Results and Internet Search Results, \
            please always prioritize local search results if both return usable results."
        else:
            # NO internet_search
            prompt = "Please give that answer based on the Local Search Results if it returns the usable results. \
            You are only allowed to use the context provided from tool_calls. Do not generate answers based on any other knowledge."
    else:
        # NO local_search
        if Config.INTERNET_SEARCH > 0:
            # AND internet_search
            prompt = "Please give that answer based on the Internet Search Results if it returns the usable results."
        else:
            # NO internet_search
            prompt = "Please give that answer based on your knowledge."
    return prompt
 
def get_language(language_code):
    language_code = language_code if language_code in Config.STT_LOCALES.split(',') else Config.LANGUAGE_DEFAULT
    language =  Config.LANGUAGES.get(language_code, Config.LANGUAGE_DEFAULT)['country']
    return language
 
@async_timeit()
async def internet_search(query, max_results=Config.INTERNET_SEARCH):
    LOGGER.info("query: {} - max_results: {}".format(query, max_results))
    params = {'q': query, 'mkt': 'en-US', "textDecorations": True, "textFormat": "HTML"}
    headers = {'Ocp-Apim-Subscription-Key': Config.BING_SUBSCRIPTION_KEY}
    response = requests.get(Config.BING_SEARCH_URL, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()
    
    images = []

    text_content = "Here is the result of internet search: \n"
    index = 1
    for search in search_results["webPages"]["value"][:max_results]:
        text_content += f"{index}. {search['name']}\n{search['snippet']}\n"
        index += 1
    return ToolResponseFormat(content=text_content, images=images)
 
@async_timeit()
async def get_embedding(text, model=Config.AZURE_OPENAI_EMB_DEPLOYMENT):
    text = text.replace("\n", " ")
    embedding_response = await AzureOpenAIClient.embeddings.create(input=[text], model=model)
    embedding = embedding_response.data[0].embedding
    return embedding
 
@async_timeit()
async def local_search(search_query, max_results=Config.LOCAL_SEARCH):
    search_query= search_query.replace("tại", "")
    search_query= search_query.replace("Madame Lân", "")
    search_query= search_query.replace("Đà Nẵng", "")
    print(search_query)
    LOGGER.info("search_query: {}".format(search_query))
    vector = VectorizedQuery(vector=await get_embedding(search_query), k_nearest_neighbors=max_results, fields="summaryVector")
    results = AzureSearchClient.search(
        search_text=search_query,
        vector_queries=[vector],
        query_type=QueryType.SEMANTIC, semantic_configuration_name='my-semantic-config',
        query_caption=QueryCaptionType.EXTRACTIVE, query_answer=QueryAnswerType.EXTRACTIVE,
        select=["summary", "content_details","image_links"],
        top=max_results
    )
    text_content = "Here is the result of local search: \n"
    index = 1
    images = []
    for result in results:
        text_content += f"{index}. {result['summary']}\n{result['content_details']}\n"
        index += 1
        print("="*40 + f"\n{result['summary']}\n" + "="*40)
        #images.append(result['image_links'])
        eranker_score = result.get('@search.reranker_score')
        print(eranker_score)
        if(float(eranker_score)>=2.3):
            images.append(result['image_links'])
 
    return ToolResponseFormat(content=text_content, images=images)
 
@async_timeit()
async def search(query):
    results = {}
    tasks = {}
    print(query)
    if Config.LOCAL_SEARCH > 0:
        tasks['local_search'] = asyncio.create_task(local_search(query))

    query += " with up-to-date knowledge from the current datetime ({}).".format(get_current_date())
    if Config.INTERNET_SEARCH > 0:
        tasks['internet_search'] = asyncio.create_task(internet_search(query))
    

    for search_type, task in tasks.items():
        try:
            result = await task
            results[search_type] = result.content.strip()
            if search_type == 'local_search':
                image_links=result.get_args('images')
            # print("@"*40 + f"\n{search_type} =====> {image_links}\n" + "@"*40)
        except Exception as exc:
            results[search_type] = f'{search_type} generated an exception: {exc}'
 
    combined_results = ""
    if Config.LOCAL_SEARCH > 0:
        local_results = results.get('local_search', '')
        combined_results = f"\nLocal Search Results (Priority):\n{local_results}"
 
    if Config.INTERNET_SEARCH > 0:
        bing_results = results.get('internet_search', '')
        combined_results += f"\nInternet Search Results:\n{bing_results}"
 
    LOGGER.info("response: {}".format(combined_results))
    image_filtration=[]
    if len(image_links) >0:
        image_filtration = image_links[0]
    return ToolResponseFormat(content=combined_results, images=image_filtration)
 
def check_args(function, args):
    sig = inspect.signature(function)
    params = sig.parameters
    for name in args:
        if name not in params:
            return False
    for name, param in params.items():
        if param.default is param.empty and name not in args:
            return False
    return True
 
FUNCTIONS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "{}".format(get_prompt_by_search_mode()),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"],
            }
        },
    },
]
 
AVAILABLE_FUNCTIONS = {
    "search": search,
}
 
class Smart_Agent():
    def __init__(self, persona, functions_spec, functions_list, engine=Config.AZURE_OPENAI_DEPLOYMENT_NAME):
        self.persona = persona
        self.engine = engine
        self.functions_spec = functions_spec
        self.functions_list = functions_list
 
    def get_current_prompt(self, language_code):
        return self.persona.format(current_date=get_current_date(), prompt_by_search_mode=get_prompt_by_search_mode(), language=get_language(language_code))
 
    @async_timeit()
    async def run(self, language_code, conversation):
        try:
            max_retries = 3
            retry_count = 0
            max_tokens = 600
            image_links = []
            while True:
                response = await AzureOpenAIClient.chat.completions.create(
                model=self.engine,
                messages=conversation,
                tools=self.functions_spec,
                tool_choice='auto',
                max_tokens=max_tokens,
                # The 'temperature' parameter controls the randomness of the output.
                # A temperature of 0.0 means the model will generate predictable, consistent, and precise responses.
                temperature=0.0
            )
                response_message = response.choices[0].message
                finish_reason = response.choices[0].finish_reason
                if finish_reason == 'content_filter':
                    retry_count += 1
                    if retry_count <= max_retries:
                        LOGGER.warning(f"Content filter triggered. Retrying {retry_count}/{max_retries}...")
                        continue
                    else:
                        raise ValueError("Content was filtered by OpenAI due to violation of content policies. Full response: {}".format(response))
                elif response_message.content is None:
                    response_message.content = ""
 
                tool_calls = response_message.tool_calls
                if tool_calls:
                    max_tokens = 300
                    conversation.append({
                        "role": response_message.role,
                        "content": response_message.content,
                        "tool_calls": response_message.tool_calls
                    })
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        if function_name not in self.functions_list:
                            conversation.pop()
                            continue
                        function_to_call = self.functions_list[function_name]
                        function_args = json.loads(tool_call.function.arguments)
                        if check_args(function_to_call, function_args) is False:
                            conversation.pop()
                            continue
                        function_response = await function_to_call(**function_args)
                        image_links = function_response.get_args('images')
                        conversation.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": function_response.content,
                            }
                        )
                    if Config.LOCAL_SEARCH > 0 and Config.INTERNET_SEARCH <= 0:
                        conversation.append({
                            "role": "system",
                            "content": "Only respond truthfully based on the retrieved information. Do not add any information that was not provided in the retrieved results."
                        })   
 
                    continue
 
                else:
                    break
            print("-"*40 + f"\n{image_links}\n" + "^"*40)
            response = response_message
            assistant_response = response.content
        except Exception as e:
            LOGGER.error("Exception: {}".format(e))
            assistant_response = Config.CHAT_EXCEPTION[language_code] if language_code in Config.CHAT_EXCEPTION else Config.CHAT_EXCEPTION_DEFAULT
            LOGGER.error("assistant_response: {}".format(assistant_response))
 
        finally:
            return assistant_response, image_links
from fastapi import APIRouter, HTTPException, Header, Body

from app.config import APP_PATH, LOGGER, async_timeit, Config
from app.core.speech import generate_speech_audio, remove_emoji, replace_markdown_links_with_urls
from app.core.agent import Smart_Agent, FUNCTIONS_SPEC, AVAILABLE_FUNCTIONS, PERSONA, AzureOpenAIClient
from app.core.authentication import check_authentication
# from app.core.prompt import IMAGE_SEARCH_PROMPT, IMAGE_SEARCH_HISTORY
from app.utils.app_exceptions import AppExceptionCase
from app.utils.service_result import ServiceResult
from app.utils.service_result import handle_result
from app.db.api import DB, Role
from threading import Thread
import asyncio
import requests

bing_subscription_key = "ac992e2236804d2b8324dee96eed10f5"
bing_endpoint = "https://api.bing.microsoft.com/v7.0/search"
bing_image = "https://api.bing.microsoft.com/v7.0/images/search"

router = APIRouter()

Agent = Smart_Agent(
    persona=PERSONA,
    functions_spec=FUNCTIONS_SPEC,
    functions_list=AVAILABLE_FUNCTIONS
)

class CustomizedMultiThread(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            if asyncio.iscoroutinefunction(self._target):
                loop = asyncio.new_event_loop()  # Create a new event loop for this thread
                asyncio.set_event_loop(loop)
                self._return = loop.run_until_complete(self._target(*self._args, **self._kwargs))
                loop.close()  # Ensure the loop is closed when finished
            else:
                self._return = self._target(*self._args, **self._kwargs)
    
    def join(self, *args):
        Thread.join(self, *args)
        return self._return


async def get_chat(access_token: str, client_id: str, user_query: str, voice_code: str) -> ServiceResult:


    try:
        user_query = user_query.strip()
        if not user_query:
            return ServiceResult(AppExceptionCase(status_code=400, context="user_query in body is required"))

        current_promt = Agent.get_current_prompt(voice_code)
        # get latest conversation
        conversation = DB.get_latest_conversations(access_token, client_id)
        conversation = [{"role": str(Role.SYSTEM), "content": current_promt}] + conversation
        conversation += [{"role": str(Role.USER), "content": user_query}]
        messages = conversation.copy()

        # ask chat
        assistant_reply, image_links = await Agent.run(voice_code, conversation)
        
        # update db ystem-prompt/user-query/assistant-reply
        DB.add_conversation(access_token, client_id, voice_code, current_promt, user_query, assistant_reply)


        # post procesing assistant-reply texts
        assistant_reply = replace_markdown_links_with_urls(assistant_reply)
        plain_text = remove_emoji(assistant_reply)
        # generate audio
        audio_path = await generate_speech_audio(plain_text, voice_code)
        audio_path = audio_path.replace(APP_PATH, "")

        # response reply by emition config
        assistant_reply = assistant_reply if Config.SEARCH_WITH_EMOTION else plain_text

        messages += [{"role": str(Role.ASSISTANT), "content": assistant_reply}]

        assistant_reply_obj = {
            "role": "assistant",
            "user_query": user_query,
            "content": assistant_reply
        }

        # @TODO update logic to get image/link here
        # image_paths = image_thread.join()
        # print('\n'.join(image_paths))
        # image_paths = await get_image_internet_search(assistant_reply)
        link_paths = []
        image_paths = image_links
        if len(image_paths) > 3:
            image_paths = image_paths[:3] 
        data={
            "assistant_reply": assistant_reply_obj,
            "audio_path": audio_path,
            "history": messages,
            "image_paths": image_paths,
            "link_paths": link_paths
        }
    except Exception as e:
        LOGGER.error("Exception: {}".format(e))
        return ServiceResult(AppExceptionCase(status_code=400, context=str(e)))
    return ServiceResult(data)

@router.post("/api/ask/{access_token}")
@async_timeit()
async def chat(access_token: str,
               ClientId: str = Header(...),
               user_query: str = Body(..., embed=True),
               voice_code: str = Body(..., embed=True)
               ):
    LOGGER.info("Request: \naccess_token={}\nclient_id={}\nvoice_code={}\nuser_query={}".format(access_token, ClientId, voice_code, user_query))
    authen = check_authentication(access_token)
    if not check_authentication(access_token).success:
        return handle_result(authen)

    response = await get_chat(access_token, ClientId, user_query, voice_code)
    LOGGER.info("Response: \naccess_token={}\nclient_id={}\nvoice_code={}\nresponse={}".format(access_token, ClientId, voice_code, response.value))
    return handle_result(response)

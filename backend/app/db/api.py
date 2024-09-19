import uuid

from fastapi import HTTPException
from azure.data.tables import TableServiceClient

from app.config import LOGGER, Config
from app.db.models.status import Status
from app.db.models.role import Role
from app.utils.utils import get_datetime_now, time2str
from app.utils.utils import uuid2str


global CURRENT_DATA, INACTIVE_DATA
CURRENT_DATA = {}
INACTIVE_DATA = {}
EMP_STR = ""
MAX_LEN = Config.HISTORY_LENGTH + 1

TableService = TableServiceClient.from_connection_string(conn_str=Config.DB_CONECTION)
TableService.create_table_if_not_exists(Config.DB_TABLE_CLIENT)
DB_CLIENT = TableService.get_table_client(table_name=Config.DB_TABLE_CLIENT)

TableService.create_table_if_not_exists(Config.DB_TABLE_CONVERSATION)
DB_CONV = TableService.get_table_client(table_name=Config.DB_TABLE_CONVERSATION)



class DB:
    """This is class to init prompt for client, add conversation by role, get latest conversations, etc.
    """
    @staticmethod
    def create_new_client_id(access_token):
        """
        Create new client id that not in GLOBAL_DB.
        Args:
        Returns:
            client_id (str): client id
        """
        client_id = uuid2str(uuid.uuid4())
        while DB.check_client_id_existed(access_token, client_id):
            client_id = uuid2str(uuid.uuid4())
        return client_id

    @staticmethod
    def init_client(access_token: str, client_id: str):
        """
        Init client with status/language/init_prompt/conversations.
        Args:
            access_token (str): access token
            client_id (str): client id
        Returns:
            dict
        """
        global CURRENT_DATA
        client = {}
        client["status"] = str(Status.ACTIVE)
        client["language"] = EMP_STR
        client["init_prompt"] = EMP_STR
        client["conversations"] = []
        client["created_at"] = get_datetime_now()
        client["updated_at"] = get_datetime_now()
        CURRENT_DATA[access_token] = CURRENT_DATA[access_token] if access_token in CURRENT_DATA else {}
        CURRENT_DATA[access_token][client_id] = client

    @staticmethod
    def create(access_token: str):
        """
        Create new client obj in GLOBAL_DB.
        Args:
            access_token (str): access token
        Returns:
            True/False
        """
        client_id = DB.create_new_client_id(access_token)
        DB.init_client(access_token, client_id)
        return client_id

    @staticmethod
    def update(access_token: str, client_id: str):
        """
        Create new client obj in GLOBAL_DB.
        Args:
            access_token (str): access token
            client_id (str): client id
        Returns:
            True/False
        """
        global CURRENT_DATA
        if not DB.check_client_id_existed(access_token, client_id):
            LOGGER.error("access_token={} - client_id={} not found!")
            raise HTTPException(status_code=400, detail="access_token={} - client_id={} not found!".format(access_token, client_id))
        CURRENT_DATA[access_token][client_id]["status"] = str(Status.INACTIVE)
        return client_id

    @staticmethod
    def check_client_id_existed(access_token: str, client_id: str):
        """
        Check if the client is existed or not.
        Args:
            access_token (str): access token
            client_id (str): client id
        Returns:
            True/False
        """
        global CURRENT_DATA
        return True if access_token in CURRENT_DATA and client_id in CURRENT_DATA[access_token] else False

    @staticmethod
    def check_client_id_active(access_token: str, client_id: str):
        """
        Check if the client is existed or not.
        Args:
            access_token (str): access token
            client_id (str): client id
        Returns:
            True/False
        """
        global CURRENT_DATA
        client = CURRENT_DATA[access_token][client_id]
        return True if client['status'] == str(Status.ACTIVE) else False

    @staticmethod
    def get_latest_conversations(access_token: str, client_id: str):
        """
        Get latest conversations client_id and limit by limit*2+1 (sytem + user/assistant).
        Args:
            access_token (str): access token
            client_id (str): client id
            limit (int): limit conversations
        Returns:
            data (list): list of latest conversations (role/content)
        """
        global CURRENT_DATA
        if not DB.check_client_id_existed(access_token, client_id):
            LOGGER.error("access_token={} - client_id={} not found!")
            DB.init_client(access_token, client_id)
            LOGGER.info("Create new access_token={} - client_id={}!")
            # raise HTTPException(status_code=400, detail="access_token={} - client_id={} not found!".format(access_token, client_id))
        if not DB.check_client_id_active(access_token, client_id):
            LOGGER.error("access_token={} - client_id={} not active!")
            raise HTTPException(status_code=400, detail="access_token={} - client_id={} not active!".format(access_token, client_id))

        client = CURRENT_DATA[access_token][client_id]
        data = []
        for d in client["conversations"][-MAX_LEN:]:
            data.append({"role": str(Role.USER), "content": d['user']})
            data.append({"role": str(Role.ASSISTANT), "content": d['assistant']})
        return data

    @staticmethod
    def add_conversation(access_token: str, client_id: str, language: str, system: str, user: str, assistant: str):
        """
        Add new conversation to DB by client_id, language, system, user, assistant.
        Args:
            access_token (str): access token
            client_id (str): client id
            language (str): language code
            system (str): system prompt
            user (str): user query
            assistant (str): system reply
        Returns:
            data (list): list of latest conversations (role/content)
        """
        global CURRENT_DATA
        if not DB.check_client_id_existed(access_token, client_id):
            LOGGER.error("access_token={} - client_id={} not found!")
            DB.init_client(access_token, client_id)
            LOGGER.info("Create new access_token={} - client_id={}!")
            # raise HTTPException(status_code=400, detail="access_token={} - client_id={} not found!".format(access_token, client_id))
        client = CURRENT_DATA[access_token][client_id].copy()
        conversation = {
                        "language": language,
                        "system": system,
                        "user": user,
                        "assistant": assistant,
                        "created_at": get_datetime_now()
                        }
        client["conversations"].append(conversation)
        client["updated_at"] = get_datetime_now()
        CURRENT_DATA[access_token][client_id] = client

    @staticmethod
    def update_status(duration=Config.STATUS_DURATION):
        """
        Update client status if inactive after duration.
        Args:
            duration (int): duration to change status time (seconds)
        Returns:
        """
        global CURRENT_DATA, INACTIVE_DATA
        try:
            LOGGER.info("Update client status if inactive after {} s.".format(duration))
            for access_token, clients in list(CURRENT_DATA.items()):
                for client_id, _ in list(clients.items()):
                    # check last updated_at of client
                    updated_at_delta = (get_datetime_now() - clients[client_id]['updated_at']).total_seconds()
                    if updated_at_delta > duration:
                        LOGGER.info("Update status of access_token={} - client_id={}".format(access_token, client_id))
                        INACTIVE_DATA[access_token] = INACTIVE_DATA[access_token] if access_token in INACTIVE_DATA else {}
                        INACTIVE_DATA[access_token][client_id] = clients[client_id]
                        INACTIVE_DATA[access_token][client_id]['status'] = str(Status.INACTIVE)
                        LOGGER.info("Remove access_token={} - client_id={} (inactive) of out the global data.".format(access_token, client_id))
                        CURRENT_DATA[access_token].pop(client_id)
        except Exception as e:
            LOGGER.error("Exception:", str(e))

    @staticmethod
    def copy_client(access_token, client_id, data):
        """
        Create client data to save DB.
        Args:
            access_token (str): access token
            client_id (str): client id
            data (dict): client data
        Returns:
            client (list): list of latest client data.
        """
        client = {}
        conversations = data["conversations"].copy()
        client["access_token"] = access_token
        client["client_id"] = client_id
        client["status"] = data["status"]
        client["created_at"] = time2str(data["created_at"])
        client["updated_at"] = time2str(data["updated_at"])
        client["language"] = conversations[0]["language"] if (len(conversations) > 0 and data["language"] == EMP_STR) else data["language"]
        client["init_prompt"] = conversations[0]["system"] if (len(conversations) > 0 and data["init_prompt"] == EMP_STR) else data["init_prompt"]
        client["PartitionKey"] = access_token
        client["RowKey"] = "{}_{}".format(client_id, client["created_at"])
        return client


    @staticmethod
    def copy_conversation(access_token, client_id, client_created_at, data):
        """
        Create conversation data to save DB.
        Args:
            access_token (str): access token
            client_id (str): client id
            client_created_at (str): create time of client
            data (dict): conversation data
        Returns:
            conv (list): list of latest conversations data.
        """
        conv = {}
        conv['client_id'] = client_id
        conv["created_at"] = time2str(data['created_at'])
        conv["language"] = data["language"]
        conv["system"] = data["system"]
        conv["user"] = data["user"]
        conv["assistant"] = data["assistant"]
        conv["PartitionKey"] = "{}_{}_{}".format(access_token, client_created_at, client_id)
        conv["RowKey"] = conv["created_at"]
        return conv

    @staticmethod
    def save_inactive_clients():
        """
        Save inactive clients to DB.
        Clear all inactive clients.
        Args:
        Returns:
        """
        global INACTIVE_DATA
        try:
            LOGGER.info("Save inactive clients to database...")
            for access_token, clients in list(INACTIVE_DATA.items()):
                for client_id, _ in list(clients.items()):
                    LOGGER.info("Save inactive client access_token={} - client_id={}".format(access_token, client_id))
                    client = DB.copy_client(access_token, client_id, clients[client_id].copy())
                    conversations = clients[client_id]["conversations"].copy()
                    try:
                        cli = DB_CLIENT.get_entity(partition_key=client["PartitionKey"], row_key=client["RowKey"])
                        DB_CLIENT.update_entity(client)
                    except Exception as e:
                        cli = DB_CLIENT.create_entity(entity=client)

                    for i in range(len(conversations)):
                        conversation = DB.copy_conversation(access_token, client_id, client["created_at"], conversations[i].copy())
                        try:
                            conv = DB_CONV.get_entity(partition_key=conversation["PartitionKey"], row_key=conversation["RowKey"])
                        except Exception as e:
                            conv = DB_CONV.create_entity(entity=conversation)
                    LOGGER.info("Saved {} conversations of access_token={} - client_id={} to database.".format(len(conversations), access_token, client_id))
            # clear all inactive clients.
            INACTIVE_DATA = {}
        except Exception as e:
            LOGGER.error("Exception:", str(e))

    @staticmethod
    def save_active_clients():
        """
        Save & update active clients to DB.
        Clear previous conversations, keep last conversations (MAX_LEN).
        Args:
        Returns:
        """
        global CURRENT_DATA
        try:
            LOGGER.info("Save & update active clients to database...")
            for access_token, clients in list(CURRENT_DATA.items()):
                for client_id, _ in list(clients.items()):
                    LOGGER.info("Save active client access_token={} - client_id={}".format(access_token, client_id))
                    client = DB.copy_client(access_token, client_id, clients[client_id].copy())
                    conversations = clients[client_id]["conversations"].copy()
                    try:
                        cli = DB_CLIENT.get_entity(partition_key=client["PartitionKey"], row_key=client["RowKey"])
                        DB_CLIENT.update_entity(client)
                    except Exception as e:
                        cli = DB_CLIENT.create_entity(entity=client)

                    for i in range(len(conversations)):
                        conversation = DB.copy_conversation(access_token, client_id, client["created_at"], conversations[i].copy())
                        try:
                            conv = DB_CONV.get_entity(partition_key=conversation["PartitionKey"], row_key=conversation["RowKey"])
                        except Exception as e:
                            conv = DB_CONV.create_entity(entity=conversation)
                    LOGGER.info("Saved {} conversations of access_token={} - client_id={} to database.".format(len(conversations), access_token, client_id))
                    # clear previous conversations, keep last conversations (MAX_LEN)
                    CURRENT_DATA[access_token][client_id]['conversations'] = conversations[-MAX_LEN:] if len(conversations) > MAX_LEN else conversations
                    LOGGER.info("Keep {} conversations of caccess_token={} - client_id={} to database.".format(len(CURRENT_DATA[access_token][client_id]['conversations']), access_token, client_id))
        except Exception as e:
            LOGGER.error("Exception:", str(e))

import argparse
import base64
import glob
import html
import io
import os
import re
import time
import json
import uuid
import logging
from bs4 import BeautifulSoup

from openai import AzureOpenAI
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import *
from azure.storage.blob import BlobServiceClient
import openai
from pypdf import PdfReader, PdfWriter
from tenacity import retry, stop_after_attempt, wait_random_exponential

# Setting up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Error log handler
error_handler = logging.FileHandler('error.log', encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)

# Info log handler
info_handler = logging.FileHandler('info.log', encoding='utf-8')
info_handler.setLevel(logging.INFO)
info_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
info_handler.setFormatter(info_formatter)

# Adding handlers to the logger
logger = logging.getLogger()
logger.addHandler(error_handler)
logger.addHandler(info_handler)

def blob_name_from_file_page(filename, folder, page=0):
    base_name = os.path.basename(filename)
    if os.path.splitext(base_name)[1].lower() == ".pdf":
        return f"{folder}/{os.path.splitext(base_name)[0]}-page-{page}.pdf"
    else:
        return f"{folder}/{base_name}"

def upload_blobs(filename, folder):
    blob_service = BlobServiceClient(account_url=f"https://{args.storageaccount}.blob.core.windows.net", credential=storage_creds)
    blob_container = blob_service.get_container_client(args.container)
    if not blob_container.exists():
        blob_container.create_container()

    if os.path.splitext(filename)[1].lower() == ".pdf":
        reader = PdfReader(filename)
        pages = reader.pages
        for i in range(len(pages)):
            blob_name = blob_name_from_file_page(filename, folder, i+1)
            print("blob name is ", blob_name)
            if args.verbose: print(f"\tUploading blob for page {i+1} -> {blob_name}")
            f = io.BytesIO()
            writer = PdfWriter()
            writer.add_page(pages[i])
            writer.write(f)
            f.seek(0)
            blob_container.upload_blob(blob_name, f, overwrite=True)
    else:
        blob_name = blob_name_from_file_page(filename, folder)
        with open(filename, "rb") as data:
            blob_container.upload_blob(blob_name, data, overwrite=True)

def remove_blobs(filename):
    if args.verbose: print(f"Removing blobs for '{filename or '<all>'}'")
    blob_service = BlobServiceClient(account_url=f"https://{args.storageaccount}.blob.core.windows.net", credential=storage_creds)
    blob_container = blob_service.get_container_client(args.container)
    if blob_container.exists():
        if filename == None:
            blobs = blob_container.list_blob_names()
        else:
            prefix = os.path.splitext(os.path.basename(filename))[0]
            blobs = filter(lambda b: re.match(f"{prefix}-\d+\.pdf", b), blob_container.list_blob_names(name_starts_with=os.path.splitext(os.path.basename(prefix))[0]))
        for b in blobs:
            if args.verbose: print(f"\tRemoving blob {b}")
            blob_container.delete_blob(b)

def remove_section_by_id(section_id):
    if args.verbose: print(f"Removing section with ID '{section_id}' from search index '{args.index}'")
    search_client = SearchClient(endpoint=f"https://{args.searchservice}.search.windows.net/",
                                 index_name=args.index,
                                 credential=search_creds)
    try:
        search_client.delete_documents(documents=[{"id": section_id}])
        print(f"Section with ID '{section_id}' removed successfully.")
    except Exception as e:
        logging.error(f"Error removing section with ID '{section_id}': {e}")
        if args.verbose: print(f"Error removing section with ID '{section_id}': {e}")
        
def remove_from_index(filename):
    if args.verbose: print(f"Removing sections from '{filename or '<all>'}' from search index '{args.index}'")
    search_client = SearchClient(endpoint=f"https://{args.searchservice}.search.windows.net/",
                                    index_name=args.index,
                                    credential=search_creds)
    while True:
        filter = None if filename == None else f"sourcefile eq '{os.path.basename(filename)}'"
        r = search_client.search("", filter=filter, top=1000, include_total_count=True)
        if r.get_count() == 0:
            break
        r = search_client.delete_documents(documents=[{ "id": d["id"] } for d in r])
        if args.verbose: print(f"\tRemoved {len(r)} sections from index")
        # It can take a few seconds for search results to reflect changes, so wait a bit
        time.sleep(2)

def remove_documents_by_sourcefile(sourcefile):
    if args.verbose:
        print(f"Removing documents with sourcefile '{sourcefile}' from search index '{args.index}'")
    
    search_client = SearchClient(
        endpoint=f"https://{args.searchservice}.search.windows.net/",
        index_name=args.index,
        credential=search_creds
    )
    
    try:
        filter = f"sourcefile eq '{sourcefile}'"
        r = search_client.search("", filter=filter, top=1000, include_total_count=True)
        total_count = r.get_count()
        
        if total_count == 0:
            print(f"No documents found with sourcefile '{sourcefile}' in the index.")
            return
        
        print(f"Found {total_count} documents with sourcefile '{sourcefile}'. Removing...")
        
        document_ids = [{ "id": d["id"] } for d in r]
        r = search_client.delete_documents(documents=document_ids)
        
        print(f"Removed {len(document_ids)} documents with sourcefile '{sourcefile}' from the index.")
        
        remove_file_from_blob_storage(sourcefile)
    
    except Exception as e:
        logging.error(f"Error removing documents with sourcefile '{sourcefile}': {e}")
        if args.verbose:
            print(f"Error removing documents with sourcefile '{sourcefile}': {e}")

def remove_file_from_blob_storage(sourcefile):
    if args.verbose:
        print(f"Removing file '{sourcefile}' from Azure Blob Storage")

    blob_service = BlobServiceClient(
        account_url=f"https://{args.storageaccount}.blob.core.windows.net", 
        credential=storage_creds
    )
    
    blob_container = blob_service.get_container_client(args.container)
    
    if blob_container.exists():
        try:
            blob_container.delete_blob(sourcefile)
            print(f"Successfully removed '{sourcefile}' from Azure Blob Storage.")
        except Exception as e:
            logging.error(f"Error removing blob '{sourcefile}': {e}")
            if args.verbose:
                print(f"Error removing blob '{sourcefile}': {e}")
    else:
        print(f"Container '{args.container}' does not exist or could not be accessed.")      

def table_to_html(table):
    table_html = "<table>"
    rows = [sorted([cell for cell in table.cells if cell.row_index == i], key=lambda cell: cell.column_index) for i in range(table.row_count)]
    for row_cells in rows:
        table_html += "<tr>"
        for cell in row_cells:
            tag = "th" if (cell.kind == "columnHeader" or cell.kind == "rowHeader") else "td"
            cell_spans = ""
            if cell.column_span and cell.column_span > 1: cell_spans += f" colSpan={cell.column_span}"
            if cell.row_span and cell.row_span > 1: cell_spans += f" rowSpan={cell.row_span}"
            table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
        table_html +="</tr>"
    table_html += "</table>"
    return table_html

def get_document_text(filename):
    offset = 0
    page_map = []
    if os.path.splitext(filename)[1].lower() == ".pdf":
        if args.localpdfparser:
            reader = PdfReader(filename)
            pages = reader.pages
            for page_num, p in enumerate(pages):
                page_text = p.extract_text()
                page_map.append((page_num, offset, page_text))
                offset += len(page_text)
        else:
            if args.verbose:
                print(f"Extracting text from '{filename}' using Azure Form Recognizer")
            form_recognizer_client = DocumentIntelligenceClient(
                endpoint=f"https://{args.formrecognizerservice}.cognitiveservices.azure.com/",
                credential=formrecognizer_creds
            )
            with open(filename, "rb") as f:
                poller = form_recognizer_client.begin_analyze_document("prebuilt-layout", analyze_request=f, content_type="application/octet-stream")
            form_recognizer_results = poller.result()

            for page_num, page in enumerate(form_recognizer_results.pages):
                tables_on_page = [table for table in form_recognizer_results.tables if table.bounding_regions and table.bounding_regions[0].page_number == page_num + 1]

                page_offset = page.spans[0].offset
                page_length = page.spans[0].length
                table_chars = [-1] * page_length
                for table_id, table in enumerate(tables_on_page):
                    for span in table.spans:
                        for i in range(span.length):
                            idx = span.offset - page_offset + i
                            if idx >= 0 and idx < page_length:
                                table_chars[idx] = table_id

                page_text = ""
                added_tables = set()
                for idx, table_id in enumerate(table_chars):
                    if table_id == -1:
                        page_text += form_recognizer_results.content[page_offset + idx]
                    elif not table_id in added_tables:
                        page_text += table_to_html(tables_on_page[table_id])
                        added_tables.add(table_id)

                page_text += " "
                page_map.append((page_num, offset, page_text))
                offset += len(page_text)
    elif os.path.splitext(filename)[1].lower() == ".txt":
        if args.verbose:
            print(f"Reading text from '{filename}'")
        with open(filename, "r", encoding="utf-8") as file:
            page_text = file.read()
            page_map.append((0, 0, page_text))
    elif os.path.splitext(filename)[1].lower() == ".html":
        page_map = get_html_text(filename)

    return page_map


def get_html_image_link(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    image_links = []
    soup = BeautifulSoup(content, "html.parser")
    images = soup.find_all("img")
    for img in images:
        image_links.append(img['src'])
    if len(image_links) > 3:
        return image_links[:3]
    return image_links


def get_html_text(filename):
    if args.verbose:
        print(f"Extracting text from HTML file: {filename}")
    with open(filename, "r", encoding="utf-8") as file:
        html_content = file.read()

    # Remove base64 image data from HTML content
    html_content = re.sub(r'<img[^>]+src="data:image/[^;]+;base64,[^"]+"[^>]*>', '', html_content)

    return [(0, 0, html_content)]

@retry(stop=stop_after_attempt(5), wait=wait_random_exponential(min=1, max=60))
def extract_topics_and_content(page_text, page_num, filename):
    sys_msg = """
    Please perform the following tasks:
    Extract Summary: Provide a concise summary of the document's content in Vietnamese. The summary should capture the main ideas and provide meaningful, contextual information.
    Content Details: Include detailed information about the document's content as a single string formatted in markdown, also in Vietnamese. The `content_details` should be a string that uses markdown syntax, including appropriate headings, bullet points, or lists for clarity.
    Extract Keywords and Entities: Identify and extract key terms and entities from the document in Vietnamese. Ensure that **no keywords or entities are duplicated** in the list. If a keyword or entity appears multiple times in the document, include it only once in the `keyword_entities` list. Additionally, make sure that all relevant keywords and entities are captured, even if they appear only once.

    Output Format: Present the extracted information in JSON format, ensuring it is well-structured and easy to read.

    Example JSON Structure:
    {  
        "summary": "Your summary here.",  
        "content_details": "### Your content details in markdown format here.",  
        "keyword_entities": ["keyword 1", "keyword 2", "entity 1", "entity 2"]  
    }
    """

    while True:
        try:
            if not page_text:
                print(f"No text found on page {page_num}. Skipping this page.")
                return {"summary": "", "content_details": "", "keyword_entities": []}
            print(f"Extracting topics and content for page {page_num+1}...")
            response = client.chat.completions.create(
                model=args.openaideployment,
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": page_text}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            response_message = response.choices[0].message.content.strip()
            logging.info(f"Raw response for page {page_num+1}: {response_message}")
            try:
                extraction = json.loads(response_message)
                if verify_json_format(extraction):
                    imgae_links = get_html_image_link(filename)
                    print(f"Extraction successful for page {page_num+1}")
                    extraction["image_links"] = imgae_links
                    return extraction
            except json.JSONDecodeError as json_error:
                logging.error(f"JSONDecodeError for page {page_num+1} of file {filename}: {json_error}")
                logging.error(f"Problematic JSON response: {response_message}")
                raise json_error
        except openai.RateLimitError:
            print("Rate limit exceeded. Retrying after 10 seconds...")
            time.sleep(10)
        except Exception as e:
            logging.error(f"Error extracting topics and content for page {page_num+1} of file {filename}: {e}")
            if 'content_filter' in str(e):
                print(f"Content filter triggered for page {page_num+1} of file {filename}. Skipping this chunk.")
                return {"summary": "", "content_details": "", "keyword_entities": []}
            else:
                raise e

def verify_json_format(data):
    required_keys = {"summary", "content_details", "keyword_entities"}
    if isinstance(data, dict):
        if not required_keys.issubset(data.keys()):
            return False
    else:
        return False
    return True

def compute_embedding(text):
    text = text.replace("\n", " ")
    while True:
        try:
            embedding_response = client.embeddings.create(input=[text], model=args.openaiembdeployment).data[0].embedding
            return embedding_response
        except openai.error.RateLimitError:
            print("Rate limit exceeded. Retrying after 10 seconds...")
            time.sleep(10)

def create_search_index():
    if args.verbose: print(f"Ensuring search index {args.index} exists")
    index_client = SearchIndexClient(endpoint=f"https://{args.searchservice}.search.windows.net/",
                                     credential=search_creds)
    if args.index not in index_client.list_index_names():
        index = SearchIndex(
            name=args.index,
            fields=[
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="summary", type=SearchFieldDataType.String),
                SearchableField(name="content_details", type=SearchFieldDataType.String),
                SearchField(name="keyword_entities", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
                SearchField(name="image_links", type=SearchFieldDataType.Collection(SearchFieldDataType.String)),
                SearchField(name="summaryVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), 
                            hidden=False, searchable=True, filterable=False, sortable=False, facetable=False,
                            vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
                SimpleField(name="sourcepage", type=SearchFieldDataType.String, filterable=True, facetable=True),
                SimpleField(name="sourcefile", type=SearchFieldDataType.String, filterable=True, facetable=True)
            ],
            semantic_search=SemanticSearch(configurations=[SemanticConfiguration(
                name="my-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="summary"),
                    content_fields=[SemanticField(field_name="content_details")],
                    keywords_fields=[SemanticField(field_name="keyword_entities")]
                )
            )]),
            vector_search=VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="myHnsw"
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name="myHnswProfile",
                        algorithm_configuration_name="myHnsw",
                    )
                ]
            )
        )
        if args.verbose: print(f"Creating {args.index} search index")
        index_client.create_index(index)
    else:
        if args.verbose: print(f"Search index {args.index} already exists")

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_from_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def filename_to_id(filename):
    filename_ascii = re.sub("[^0-9a-zA-Z_-]", "_", filename)
    filename_hash = base64.b16encode(filename.encode('utf-8')).decode('ascii')
    return f"file-{filename_ascii}-{filename_hash}"    

def insert_into_azure_search(extraction, filename, folder, page_num=None):
    if page_num is not None:
        print(f"Inserting data into Azure Search for '{filename}-page-{page_num}'")
        doc_id = f"{filename_to_id(filename)}-page-{page_num}"
        sourcepage = blob_name_from_file_page(filename, folder, page_num)
    else:
        print(f"Inserting data into Azure Search for '{filename}'")
        doc_id = filename_to_id(filename)
        sourcepage = blob_name_from_file_page(filename, folder)
        
    search_client = SearchClient(
        endpoint=f"https://{args.searchservice}.search.windows.net/",
        index_name=args.index,
        credential=search_creds
    )
    
    document = {
        "id": doc_id,
        "summary": extraction["summary"],
        "content_details": extraction["content_details"],
        "keyword_entities": extraction['keyword_entities'],
        "image_links": extraction["image_links"],
        "summaryVector":compute_embedding(extraction['summary']),
        "sourcepage": sourcepage,
        "sourcefile": f"{folder}/{filename}"
    }
    
    search_client.upload_documents([document])
    print(f"Inserted document into Azure Search")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prepare documents by extracting content from PDFs, extracting topics, types, and content using Azure OpenAI, and indexing in a search index.",
        epilog="Example: prepdocs.py '..\data\*' --storageaccount myaccount --container mycontainer --searchservice mysearch --index myindex -v"
    )
    parser.add_argument("folder", help="Folder containing files to be processed")
    parser.add_argument("--skipblobs", action="store_true", help="Skip uploading individual pages to Azure Blob Storage")
    parser.add_argument("--storageaccount", help="Azure Blob Storage account name")
    parser.add_argument("--container", help="Azure Blob Storage container name")
    parser.add_argument("--storagekey", required=False, help="Optional. Use this Azure Blob Storage account key instead of the current user identity to login (use az login to set current user for Azure)")
    parser.add_argument("--tenantid", required=False, help="Optional. Use this to define the Azure directory where to authenticate)")
    parser.add_argument("--searchservice", help="Name of the Azure Cognitive Search service where content should be indexed (must exist already)")
    parser.add_argument("--index", help="Name of the Azure Cognitive Search index where content should be indexed (will be created if it doesn't exist)")
    parser.add_argument("--searchkey", required=False, help="Optional. Use this Azure Cognitive Search account key instead of the current user identity to login (use az login to set current user for Azure)")
    parser.add_argument("--openaiservice", help="Name of the Azure OpenAI service used to compute embeddings")
    parser.add_argument("--openaiembdeployment", help="Name of the Azure OpenAI model deployment for an embedding model ('text-embedding-ada-002' recommended)")
    parser.add_argument("--openaideployment", help="Name of the Azure OpenAI model deployment for an gpt model ('gpt-40' recommended)")
    parser.add_argument("--novectors", action="store_true", help="Don't compute embeddings for the sections (e.g. don't call the OpenAI embeddings API during indexing)")
    parser.add_argument("--openaikey", required=False, help="Optional. Use this Azure OpenAI account key instead of the current user identity to login (use az login to set current user for Azure)")
    parser.add_argument("--remove", action="store_true", help="Remove references to this document from blob storage and the search index")
    parser.add_argument("--removeall", action="store_true", help="Remove all blobs from blob storage and documents from the search index")
    parser.add_argument("--removeid", help="Remove a section by its ID from the search index")
    parser.add_argument("--removesourcefile", help="Remove documents by the sourcefile field from the search index")
    parser.add_argument("--localpdfparser", action="store_true", help="Use PyPdf local PDF parser (supports only digital PDFs) instead of Azure Form Recognizer service to extract text, tables and layout from the documents")
    parser.add_argument("--formrecognizerservice", required=False, help="Optional. Name of the Azure Form Recognizer service which will be used to extract text, tables and layout from the documents (must exist already)")
    parser.add_argument("--formrecognizerkey", required=False, help="Optional. Use this Azure Form Recognizer account key instead of the current user identity to login (use az login to set current user for Azure)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    default_creds = None
    search_creds = default_creds if args.searchkey == None else AzureKeyCredential(args.searchkey)

    use_vectors = not args.novectors

    if not args.skipblobs:
        storage_creds = default_creds if args.storagekey == None else args.storagekey
    if not args.localpdfparser:
        if args.formrecognizerservice == None:
            print("Error: Azure Form Recognizer service is not provided. Please provide formrecognizerservice or use --localpdfparser for local pypdf parser.")
            exit(1)
        formrecognizer_creds = default_creds if args.formrecognizerkey == None else AzureKeyCredential(args.formrecognizerkey)

    if use_vectors:
        client = AzureOpenAI(
            api_key=args.openaikey,  
            api_version="2023-12-01-preview",
            azure_endpoint=f"https://{args.openaiservice}.openai.azure.com"
        )

    if args.removeall:
        remove_blobs(None)
        remove_from_index(None)
    elif args.removeid:
        remove_section_by_id(args.removeid)
    elif args.removesourcefile:
        remove_documents_by_sourcefile(args.removesourcefile)
    else:
        if not args.remove:
            create_search_index()

        print(f"Processing files in folder: {args.folder}")
        file_pattern = os.path.join(args.folder, '*')
        files = glob.glob(file_pattern)
        print(f"Found {len(files)} files: {files}")

        for filename in files:
            try:
                if not os.path.isfile(filename):
                    print(f"File '{filename}' not found. Skipping.")
                    continue
                if args.verbose: print(f"Processing '{filename}'")
                if args.remove:
                    remove_blobs(filename)
                    remove_from_index(filename)
                elif args.removeall:
                    remove_blobs(None)
                    remove_from_index(None)
                else:
                    folder_name = os.path.basename(args.folder)
                    if not args.skipblobs:
                        print(f"Uploading blobs for '{filename}'")
                        upload_blobs(filename, folder_name)
                    page_map = get_document_text(filename)

                    if os.path.splitext(filename)[1].lower() == ".pdf":
                        for page_num, offset, page_text in page_map:
                            extraction = extract_topics_and_content(page_text, page_num, filename)
                            base_filename = os.path.basename(filename)
                            insert_into_azure_search(extraction, base_filename, folder_name, page_num+1)
                            time.sleep(10)
                    else:
                        page_text = page_map[0][2]
                        extraction = extract_topics_and_content(page_text, 0, filename)
                        base_filename = os.path.basename(filename)
                        insert_into_azure_search(extraction, base_filename, folder_name)

            except Exception as e:
                logging.error(f"Error processing file {filename}: {e}")
                if args.verbose: print(f"Error processing file {filename}: {e}")
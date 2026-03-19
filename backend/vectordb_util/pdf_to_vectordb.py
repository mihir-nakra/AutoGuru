from vectordb_util.pdf_util import extract_into_text_docs
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_aws import ChatBedrockConverse
from langchain_core.documents import Document
import os

def create_vectordbs_from_pdf(file_path, output_folder, embedding_path):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    file_path = os.path.abspath(file_path)
    extract_into_text_docs(file_path, output_folder)
    texts = _get_split_docs(output_folder)
    sum_texts = _get_summarized_texts(texts)
    _delete_docs(output_folder)
    embeddings = HuggingFaceEmbeddings(cache_folder=embedding_path)
    _create_db(output_folder, 'full_db', embeddings, texts)
    _create_db(output_folder, 'sum_db', embeddings, sum_texts)


def _get_split_docs(file_path):
    loader = DirectoryLoader(file_path, glob="./*.txt", loader_cls=TextLoader, show_progress=True)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    return texts

def _create_db(file_path, name, embeddings, texts):
    persist_directory = file_path + "/" + name
    Chroma.from_documents(documents=texts,
                          embedding=embeddings,
                          persist_directory=persist_directory)

def _delete_docs(file_path):
    file_list = os.listdir(file_path)

    # Iterate through the files and remove text files
    for filename in file_list:
        if filename.endswith(".txt"):
            temp = os.path.join(file_path, filename)
            os.remove(temp)

def _get_summarized_texts(texts):
    region = os.environ.get("AWS_REGION", "us-east-1")
    llm = ChatBedrockConverse(
        model="openai.gpt-oss-20b-1:0",
        region_name=region,
    )
    summarized_texts = []
    count = 0
    for text in texts:
        response = llm.invoke(
            f"Summarize the following text concisely, preserving key facts and details:\n\n{text.page_content}"
        )
        content = response.content
        if isinstance(content, list):
            content = " ".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            ).strip()
        count += 1
        print(f"Summarized chunk {count}/{len(texts)}")
        summarized_texts.append(Document(page_content=content, metadata=text.metadata))

    return summarized_texts

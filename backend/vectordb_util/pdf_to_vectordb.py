from vectordb_util.pdf_util import extract_into_text_docs
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from transformers import pipeline
from langchain.schema import Document
import torch
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
    loader = DirectoryLoader(file_path, glob="./*.txt", show_progress=True)
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
    summarizer = pipeline("summarization", model="./bart-large-cnn-model", tokenizer="./bart-large-cnn-tokenizer", device='cuda' if torch.cuda.is_available() else 'cpu')
    summarized_texts = []
    count = 0
    for text in texts:
        content = summarizer(text.page_content, max_length=1028, min_length=64, do_sample=False, num_beams=5)
        sum_text = content[0]['summary_text']
        count += 1
        print(f"Done with page {count}")
        summarized_texts.append(Document(page_content=sum_text, metadata=text.metadata))
    
    return summarized_texts
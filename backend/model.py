from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import HuggingFacePipeline
import os
from huggingface_hub import InferenceClient
from threading import Thread
import torch
from transformers import AutoTokenizer, pipeline, AutoModelForSeq2SeqLM, TextIteratorStreamer

class Model:
    def __init__(self, use_local=True, verbose=False):
        torch.cuda.empty_cache()

        if verbose: print("initializing model")

        if use_local:
            model_id = './google-flan-t5'
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_id, load_in_8bit=False)
            self.streamer = TextIteratorStreamer(tokenizer=tokenizer)

            if verbose: print("intializing pipeline")
            pipe = pipeline(
                "text2text-generation",
                model=model,
                tokenizer=tokenizer,
                max_length=512,
                device='cuda' if torch.cuda.is_available() else 'cpu',
                streamer=self.streamer
            )

            self.llm = HuggingFacePipeline(pipeline=pipe)
        else:
            self.llm = InferenceClient(model='google/flan-t5-large')


        self.use_local = use_local

        # Create vector database
        if verbose: print("intializing embeddings")
        self.embeddings = HuggingFaceEmbeddings(cache_folder="./embedding")

        if verbose: print("initialization done")

    def inference(self, prompt, context, verbose=False):
        template = self._get_prompt(prompt, context)
        if verbose: print(template)
        if self.use_local:
            answer = self.llm(template)
        else:
            answer = self.llm.text_generation(template, max_new_tokens=512)
        
        return answer

    
    def get_context(self, prompt, db_id, useBoth=True):
        sum_db, full_db = self._load_vectordbs(db_id)

        res = []
        if useBoth:
            res = sum_db.similarity_search(prompt, k=4) + full_db.similarity_search(prompt, k=4)
        else:
            res = sum_db.similarity_search(prompt, k=4)

        return res
    

    def _load_vectordbs(self, db_id):
        full_db = Chroma(persist_directory=f"./vectordbs/{db_id}/full_db",
                            embedding_function=self.embeddings)
        sum_db = Chroma(persist_directory=f"./vectordbs/{db_id}/sum_db",
                            embedding_function=self.embeddings)

        return sum_db, full_db
        
    
    def stream_inference(self, prompt, context, verbose=False):
        if self.use_local:
            thread = Thread(target=self.inference, kwargs={'prompt': prompt, 'context': context})
            thread.start()
            generated_text = "" 
            for new_text in self.streamer:
                formatted = new_text
                formatted = formatted.replace("<pad> ", "")
                formatted = formatted.replace("<pad>", "")
                formatted = formatted.replace("</s>", "")
                yield formatted
        else:
            for token in self.llm.text_generation(prompt, max_new_tokens=512, stream=True):
                yield token

    def _get_prompt(self, prompt, context):
        # Private method to generate a template based on the input prompt

        contextStr = ""
        for item in context:
            contextStr += item['page_content']

        template = f"""
    You are a helpful auto mechanic that can answer questions based on certain knowledge. 
    Here is the knowledge you have: {contextStr}

    Now answer the following question: {prompt}

    If you don't have enough information say you "I don't have enough information, but click view source below to check the manual"

        """

        return template
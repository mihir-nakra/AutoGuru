# Car Manual LLM
Overview: This project utilizes large language models and vector databases to be able to answer questions about a specific make and model of a car by searching its manual for information
\
\
Note: I included the vector databases in the repository, but did not include any of the models since they were too large and it didn't make sense to include. The models not included are 
the __google/flan-t5-large__, __embedding__, __bart-large-cnn__, and __bart-large-cnn-tokenizer__. 

## I. Introduction
I had the idea for this project when I was driving from Austin to Dallas and got stuck with a flat tire in a random McDonald's parking lot. I'd never changed a tire before, and in that moment 
I realized how helpful it would be if I could ask someone specific things about my car, like where the reinforced areas are, or how strong of a jack I needed. That thought led me to creating 
this website, which allows a user to select their car's make and model, and ask specific questions about it. I'd never done something like this before, so this project was also a great
learning opportunity for me.

## II. Making the Pipeline

### i. Figuring out what model to use
At the start of this project, I didn't know very much about large language models or all the different types there are. I watched a lot of videos and looked at a lot of tutorials, and settled 
on using the google flan t5 large model from HuggingFace. I chose this model because it was really good at text to text generation, and it wasn't to big that my computer couldn't run it locally.

### ii. Adding in the car manual information
Now that I found a good model, I had to figure out a way to get it relevant information so that it can answer questions effectively. I found the car manuals online, but there was a long process
of trial and error to figure out the best way to extract information from it. The method I ended up using was to split the pdf into individual text documents for each page, and then use the 
RecursiveCharacterTextSplitter from langchain in order to split the text into reasonably sized chunks. Then, I would take those chunks and load them into a vector database using the default 
embedding model provided by HuggingFace. The vector database I used was ChromaDB through langchain. In addition to taking the raw split text and putting it into a vector database, I also 
use the bart large cnn model to summarize each chunk in order to make it easier for the model to use the data later on. Each summarized chunk was put into another vector database, and both 
databases were used when searching for context. The reason I split each pdf page into its own text document is so that the page source could be identified, and the user could visit those pages 
for more information. 

### iii. Putting it all together
At this point I had a model, and I had vector databases to be able to provide context, and all I had to do was put it together. The workflow for the process from asking the question to 
receiving an answer looks like this:

1. User asks the question
2. A similarity search is performed on both vector databases for this specific manual and the context / knowledge for the model is obtained
3. The context / knowledge and the question are combined into one prompt for the large language model
4. The model returns an answer

## Making it Usable

### i. Abstracting the Model
At this point I had a working pipeline to get answers to questions, but it wasn't very usable. In order to make it usable, I first created a class for the model in backend/model.py so that 
all the inferencing logic could be contained in it and the API I was going to create wouldn't have to worry about handling that logic. I don't think it's necessary to dive super 
deep into the class, but I wanted to explain my thought process for creating it.

### ii. Creating an API
Since I planned to create a frontend in React, I needed to make an API so that the frontend could access the model. I used flask to make the API, and defined a few 
routes in order to initialize the model, get context, and stream the inference. The logical flow of operations to the API looks like this:

1. Client calls /init and if the model hasn't been initialized it is (intialization includes loading in the large language model and embedding model)
2. Client passes in a prompt and car information to /get-context in order to get the context data and sources from the vector databases*
3. Client passes in the prompt and context to /stream-inference, which will stream the response from the model back to the client to ensure a smooth experience for the user

\* I split the logic into two calls, /get-context and /stream-inference so that the client would have access to the page sources from the context, and could use those to tell the user where 
the information came from. Otherwise, the client would have no way to access the sources and that capability wouldn't exist.

### ii. Making the Frontend
Now that I had the backend finished, I needed to connect it with a frontend that the user could actually use. I won't go super detailed in describing how I made it, but the gist is that
I used React and the Mantine UI library to quickly put up a nice frontend. From there, all I had to do was call my API routes and ensure the logic worked.

## Conclusion

### i. Files
Here I'll just go through and explain the purpose of the files I haven't talked about yet:
* backend/vectordb_util: These files are for turning a pdf manual into the full and summary vector databases. The only method you would need is create_vector_dbs_from_pdf in pdf_to_vectordb.py,
and calling that will take care of creating those databases
* frontend/Controllers/api_interactions.js: As the name suggests, this file is for interacting with the API, taking that logic out of the React files.
* frontend/Controllers/vehicle_info.js: This file just holds an object that has information about the currently supported vehicle's and years in the website so the car selection isn't hardcoded.
* frontend/Controllers/select_controller.js: This file interacts with vehicle_info.js to define some helper methods for the frontend to populate the selection dropdowns.

### ii. What I got from this project
At the start of this project I didn't know much about large language models at all, but at the end I feel a lot more comfortable with the concept and am exciting to continue learning 
about all the capabilities. I had a lot of fun creating this project and am happy with how it turned out.






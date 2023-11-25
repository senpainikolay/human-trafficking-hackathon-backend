from PyPDF2 import PdfReader 
import os
import openai 
from scipy.spatial.distance import cosine 

from dotenv import load_dotenv

load_dotenv()



OPENAI_API_KEY = os.getenv("API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)


def  sumarize_text(text):
    text_array = text.split()
    max_elements = 6000
    chunks = [' '.join(text_array[i : i + max_elements]) for i in range(0, len(text_array), max_elements)] 



    prev_context = ''

    prompt = f"I need you to summarize the following text. The text is in romanian and the summary should be in romanian: {chunks[0]}" 
    for i in range(len(chunks)):

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-3.5-turbo-16k",
            temperature=1
        )
        prev_context = chat_completion.choices[0].message.content
        try:
            prompt = f"Given the previous summarized text: {prev_context}, Sumarize the next text chunk: {chunks[i+1]}. Translate that in romanian. "
        except:
            pass 

        if len(chunks)-1 == i:
            chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f'Give back a json string of "text" : " {prev_context}", "title" : make a short title, "description" : make a short description',
                }
            ],
            model="gpt-3.5-turbo-16k",
            temperature=0
          ) 
            prev_context = chat_completion.choices[0].message.content



    return prev_context 



def __get_embedding(text, model="text-embedding-ada-002"):
   text = text.replace("\n", " ")
   return client.embeddings.create(input = [text], model=model).data[0].embedding

def find_similarity(text1, text2):
    embedding1 = __get_embedding(text1)
    embedding2 = __get_embedding(text2)

    return 1 - cosine(embedding1, embedding2)
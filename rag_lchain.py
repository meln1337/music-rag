from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage, AIMessage
import torch
import gradio as gr
import sys
from pinecone.grpc import PineconeGRPC as Pinecone
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain.retrievers import ContextualCompressionRetriever
from pinecone_text.sparse import BM25Encoder
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import PineconeHybridSearchRetriever

import nltk

nltk.download('punkt')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

print(f"Device: {device}")

bm25 = BM25Encoder().load("sparse_encoder.json")
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
print('Pulled embedding model')
bge_reranker = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")
print('Pulled cross-encoder model')
compressor = CrossEncoderReranker(model=bge_reranker, top_n=3)

system_prompt = """\
            You are an intelligent assistant designed to provide accurate and relevant answers based on the provided context.

            Rules:
            - Always analyze the provided context thoroughly before answering.
            - Respond with factual and concise information.
            - If context is ambiguous or insufficient or you can't find answer, say 'I don't know.'
            - Do not speculate or fabricate information beyond the provided context.
            - Follow user instructions on the response style(default style is detailed response if user didn't provide any specifications):
              - If the user asks for a detailed response, provide comprehensive explanations.
              - If the user requests brevity, give concise and to-the-point answers.
            - When applicable, summarize and synthesize information from the context to answer effectively.
            - Avoid using information outside the given context.
          """

class QABot:
    def __init__(self, retriever):
        self.retriever = retriever

    def set_retriever(self, retriever):
        self.retriever = retriever

    def answer_question(self, question):
        if len(bm25.encode_queries(question)['values']) == 0:
            return "BM25 embedded this query as an empty list, please use other query"

        self.chat = [
            SystemMessage(
                system_prompt
            )
        ]
        results = self.retriever.invoke(question)

        for i, match in enumerate(results[:1]):
            print(f'\n\nMatch: {i}\n:{match}')

        context = '\n'.join([el.page_content for el in results[:1]])

        self.chat.append(
            SystemMessage(f"""
            Context information is below.
            ---------------------
            {context}
            ---------------------
            Given the context information and not prior knowledge, answer the query.
            """
            )
        )

        self.chat.append(
            HumanMessage(question)
        )

        answer = llm.invoke(self.chat)

        answer.content += f"\n\nSource: [{results[0].metadata['source']}]"
        answer.content += f"\nChunks before reranking: [{', '.join([f'{idx + 1}. {results[idx].metadata['id']}' for idx in range(len(results))])}]"""
        answer.content += f"\nChunks after reranking: [{results[0].metadata['id']}]\n"

        if 'url' in results[0].metadata:
            answer.content += f"URL: {results[0].metadata['url']}"

        print(f'\n\nAnswer: {answer}\n\n')

        self.chat.append(
            AIMessage(answer.content)
        )

        print(f"Length of chat after answering: {len(self.chat)}")

        return answer.content

pinecone_client = None
groq_client = None
pc = None
hybrid_compression_retriever = None
dense_compression_retriever = None
sparse_compression_retriever = None
llm = None
bot = None

def initialize_clients(pinecone_key, groq_key):
    global bot, pinecone_client, groq_client, pc, hybrid_compression_retriever, dense_compression_retriever, sparse_compression_retriever, llm

    try:
        # Initialize Pinecone client
        pc = Pinecone(api_key=pinecone_key)
        index_name = "rag-llm"
        namespace = "embedded-texts"
        index = pc.Index(index_name)

        hybrid_vector_store = PineconeHybridSearchRetriever(
            index=index,
            embeddings=embedding,
            sparse_encoder=bm25,
            namespace=namespace,
            top_k=3,
            alpha=0.7
        )

        hybrid_compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=hybrid_vector_store
        )

        dense_vector_store = PineconeHybridSearchRetriever(
            index=index,
            embeddings=embedding,
            sparse_encoder=bm25,
            namespace=namespace,
            top_k=3,
            alpha=1
        )

        dense_compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=dense_vector_store
        )

        sparse_vector_store = PineconeHybridSearchRetriever(
            index=index,
            embeddings=embedding,
            sparse_encoder=bm25,
            namespace=namespace,
            top_k=3,
            alpha=0
        )

        sparse_compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=sparse_vector_store
        )

        llm = ChatGroq(temperature=1, model_name="llama3-8b-8192",
                       groq_api_key=groq_key)

        print('Connected to Groq API Provider of LLaMA')

        bot = QABot(retriever=hybrid_compression_retriever)

        return "Clients initialized successfully!"
    except Exception as e:
        return f"Error initializing clients: {e}"

def response(mode, message):
    try:
        if message == "/exit":
            gr.close_all()
            print('Finishing the program')
            sys.exit(0)

        # Set retriever based on mode
        if mode == "Hybrid":
            bot.set_retriever(hybrid_compression_retriever)
        elif mode == "Dense":
            bot.set_retriever(dense_compression_retriever)
        elif mode == "Sparse":
            bot.set_retriever(sparse_compression_retriever)

        answer = bot.answer_question(message)
        return answer
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    def check_inputs(pinecone_key, groq_key, mode, input_text):
        return bool(pinecone_key and groq_key and mode and input_text)


    with gr.Blocks(title="Music-based RAG Application") as app:
        gr.Markdown("# Music-based RAG application based on LLaMa, Langchain, Pinecone")
        gr.Markdown(
            "Welcome to my RAG application that specializes in music. More precisely, on some of the artists I talked about on the Genius website: https://genius.com/. I scrapped their website and extracted info about artist and their most popular songs (maximum 100).")
        gr.Markdown("""
                - List of 48 available artists:\n
                    - Nu-metal: Deftones, Linkin Park, Korn, Slipknot, System of A Down, Limp Bizkit\n
                    - Shoegaze: Superheaven, Slowdive, Sunny Day Real Estate, Title Fight\n
                    - Punk rock: Blink 182, Sum 41, DUCKBOY\n
                    - Rap: Bones, A$AP Rocky, Travis Scott, Lil Uzi Vert, Future, $uicideboy$, Yeat, Playboi Carti, Kanye West, Lil Peep, Kendrick Lamar, 21 Savage, Destroy Lonely, Ken Carson, Bladee, Yung Lean, J. Cole, Eminem, Young Thug, Gunna\n
                    - Electronic music: Crystal Castles, Snow Strippers\n
                    - Other: Nirvana, Bring Me The Horizon, Misfits, The Smiths, Evanescence, Twin Tribes, TOOL, Metallica, Joy Division, Lebanon Hanover, The Cure, Marilyn Manson, The Weeknd
                """)
        gr.Markdown(
            "Feel free to ask question! My project is described in more detail in my GitHub repository: https://github.com/meln1337/music-rag")

        gr.Markdown("""
            - Examples of questions:\n
                - Who is rapper Bones?\n
                - What are the alternate names of Bones?
        """)

        with gr.Row():
            pinecone_key = gr.Textbox(label="Pinecone API Key", placeholder="Enter your Pinecone API key here")
            groq_key = gr.Textbox(label="Groq API Key", placeholder="Enter your Groq API key here")
            init_button = gr.Button("Submit API Keys")
            output_api_keys = gr.Textbox(label="Output API keys", lines=4, interactive=False)

        mode = gr.Radio(
            value="Hybrid",
            choices=["Dense", "Sparse", "Hybrid"],
            label="Select Retriever Mode",
        )

        input_text = gr.Textbox(label="Input Text", placeholder="Enter your text here", lines=2)
        output = gr.Textbox(label="Output", lines=4, interactive=False)
        submit_button = gr.Button("Submit Query", interactive=False)

        # Link initialization button to client setup
        init_button.click(
            initialize_clients,
            inputs=[pinecone_key, groq_key],
            outputs=output_api_keys
        )


        # Enable the submit button only after initialization
        def enable_submit_button():
            return gr.update(interactive=True)


        init_button.click(enable_submit_button, outputs=submit_button)

        # Link query submission to response
        submit_button.click(
            response,
            inputs=[mode, input_text],
            outputs=output
        )

    app.launch()
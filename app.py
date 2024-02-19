import streamlit as st
import PyPDF2
from io import StringIO
import torch
from auto_gptq import AutoGPTQForCausalLM
from langchain import HuggingFacePipeline, PromptTemplate
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from pdf2image import convert_from_path
from transformers import AutoTokenizer, TextStreamer, pipeline
import os

# Check if CUDA is available
device = torch.device("cpu")


# Initialize Streamlit UI
st.title("PDF Extractor")

file = st.file_uploader("Upload a PDF file", type="pdf")

# Check for user input and execute the model

    # Data loading
if file is not None:
    
    pdf_reader = PyPDF2.PdfReader(file)
    content = ""

    for page in range(len(pdf_reader.pages)):
        content += pdf_reader.pages[page].extract_text()

    embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-large", model_kwargs={"device": device})

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=64)
    texts = text_splitter.create_documents(content)

    # Model loading
    model_name_or_path = "TheBloke/Llama-2-13B-chat-GPTQ"
    model_basename = "model"
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)
    gptq_config = GPTQConfig(bits=4, dataset = "c4", tokenizer=tokenizer)
    model = AutoGPTQForCausalLM.from_quantized(
        model_name_or_path,
        revision="gptq-4bit-128g-actorder_True",
        model_basename=model_basename,
        use_safetensors=True,
        trust_remote_code=True,
        inject_fused_attention=False,
        device=device,
        quantize_config=gptq_config,
    )


    # Pipeline setup
    streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    text_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=1024, temperature=0,
                             top_p=0.95, repetition_penalty=1.15, streamer=streamer)
    llm = HuggingFacePipeline(pipeline=text_pipeline, model_kwargs={"temperature": 0})

    # Generate response
    response = llm("Generate a JSON containing all important information and key values as given in the document")
    st.write("JSON Generated:", response)

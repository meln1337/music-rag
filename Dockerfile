FROM python:3.12

WORKDIR /APP

COPY requirements.txt .
COPY sparse_encoder.json .
COPY README.md .
RUN pip install --no-cache-dir -r requirements.txt

COPY rag_lchain.py .

EXPOSE 7860

ENV GRADIO_SERVER_NAME="0.0.0.0"

CMD ["python", "rag_lchain.py"]
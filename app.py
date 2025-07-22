import os
import pdfplumber
import faiss
import requests
import numpy as np
from flask import Flask, request, render_template_string, redirect, url_for, flash, session, jsonify
from slack_sdk.web import WebClient
from slack_sdk.signature import SignatureVerifier
import openai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "supersecret")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

slack_client = WebClient(token=SLACK_BOT_TOKEN)
signature_verifier = SignatureVerifier(SLACK_SIGNING_SECRET)
openai.api_key = OPENAI_API_KEY

PDF_FOLDER = "data/pdfs"
INDEX_FILE = "faiss.index"
CHUNK_SIZE = 1000

index = None
texts = []

from pdf_utils import extract_text_from_pdf, chunk_text
from vector_store import embed_text, build_faiss_index, save_faiss_index, load_faiss_index, save_texts, load_texts, search_index

def reindex_all_pdfs():
    global texts, index

    os.makedirs(PDF_FOLDER, exist_ok=True)
    all_text_chunks = []

    for filename in os.listdir(PDF_FOLDER):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(PDF_FOLDER, filename)
            try:
                text = extract_text_from_pdf(filepath)
                chunks = chunk_text(text, max_len=CHUNK_SIZE)
                all_text_chunks.extend(chunks)
            except Exception as e:
                print(f"[ERRO] Falha ao processar {filename}: {e}")

    texts = all_text_chunks
    embeddings = embed_text(texts)
    index = build_faiss_index(embeddings)
    save_faiss_index(index)
    save_texts(texts)
    print(f"[INFO] Reindexados {len(texts)} chunks de {len(os.listdir(PDF_FOLDER))} arquivos.")

url = "https://smartpdf.com.br/DIFERENCA_ENTRE_O_SIGILO_FINANCEIRO_fiscal.pdf"
response = requests.get(url)

if response.status_code == 200:
    with open("downloaded.pdf", "wb") as f:
        f.write(response.content)
    print("PDF downloaded successfully.")

    os.makedirs(PDF_FOLDER, exist_ok=True)
    downloaded_path = os.path.join(PDF_FOLDER, "downloaded.pdf")
    os.replace("downloaded.pdf", downloaded_path)

    text = extract_text_from_pdf(downloaded_path)
    chunks = chunk_text(text, max_len=CHUNK_SIZE)
    previous_texts = load_texts() if os.path.exists("texts.pkl") else []
    combined_texts = previous_texts + chunks
    texts = combined_texts

    embeddings = embed_text(combined_texts)
    index = build_faiss_index(embeddings)
    save_faiss_index(index)
    save_texts(combined_texts)

    print(f"[DEBUG] downloaded.pdf processado e indexado com {len(chunks)} chunks.")
else:
    print(f"Failed to download PDF. Status code: {response.status_code}")

@app.before_request
def require_login():
    if request.endpoint in ['upload_pdf', 'upload_form'] and not session.get('logged_in'):
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        pwd = request.form.get('password')
        if pwd == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('upload_form'))
        else:
            flash("Wrong password", "danger")
    return render_template_string("""
        <h2>Login</h2>
        <form method="post">
            <input type="password" name="password" placeholder="Password" required/>
            <button type="submit">Login</button>
        </form>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <ul>{% for category, msg in messages %}
                <li style="color:red;">{{ msg }}</li>
            {% endfor %}</ul>
          {% endif %}
        {% endwith %}
    """)

@app.route('/upload', methods=['GET'])
def upload_form():
    # List PDFs in the folder
    pdfs = []
    if os.path.exists(PDF_FOLDER):
        pdfs = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')]
    return render_template_string("""
        <h2>Upload PDFs</h2>
        <form action="{{ url_for('upload_pdf') }}" method="post" enctype="multipart/form-data">
            <input type="file" name="pdf_files" accept=".pdf" multiple required/>
            <button type="submit">Upload</button>
        </form>
        <h3>Uploaded PDFs</h3>
        <ul>
        {% for pdf in pdfs %}
            <li>{{ pdf }} <form style="display:inline;" action="{{ url_for('remove_pdf', filename=pdf) }}" method="post"><button type="submit">Remove</button></form></li>
        {% endfor %}
        </ul>
    """, pdfs=pdfs)

@app.route('/remove_pdf/<filename>', methods=['POST'])
def remove_pdf(filename):
    filepath = os.path.join(PDF_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Removed {filename}", "success")
    else:
        flash(f"File {filename} not found", "danger")
    return redirect(url_for('upload_form'))

@app.route('/upload', methods=['POST'])
def upload_pdf():
    files = request.files.getlist('pdf_files')
    if not files:
        flash("No files uploaded", "danger")
        return redirect(url_for('upload_form'))

    os.makedirs(PDF_FOLDER, exist_ok=True)
    all_text_chunks = []

    for f in files:
        filename = f.filename
        filepath = os.path.join(PDF_FOLDER, filename)
        f.save(filepath)
        text = extract_text_from_pdf(filepath)
        chunks = chunk_text(text, max_len=CHUNK_SIZE)
        all_text_chunks.extend(chunks)

    global index, texts

    # 🔄 Carrega os textos e índice anteriores, se existirem
    previous_texts = load_texts() if os.path.exists("texts.pkl") else []
    combined_texts = previous_texts + all_text_chunks
    texts = combined_texts

    embeddings = embed_text(combined_texts)
    index = build_faiss_index(embeddings)
    save_faiss_index(index)
    save_texts(combined_texts)

    flash(f"{len(files)} PDFs adicionados à base de conhecimento.", "success")
    return redirect(url_for('upload_form'))

@app.route('/slack/events', methods=['POST'])
def slack_events():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return "Invalid signature", 400

    data = request.form
    user_question = data.get('text')

    if not user_question:
        return jsonify({"text": "Por favor coloque uma pergunta após o comando."})

    global index, texts
    if index is None or len(texts) == 0:
        return jsonify({"text": "A base de conhecimento está vazia. O administrador deve fazer upload de PDFs primeiro"})

    context_chunks = search_index(user_question, index, texts, top_k=3)
    context_text = "\n\n".join(context_chunks)

    prompt = [
        {"role": "system", "content": "Você responde perguntas baseadas apenas no documentos providenciados. Procure e leia atentamente cada documento para que uma pergunta simples não passe despercebida. Se não for possível achar a resposta, simplesmente responda 'Informação não encontrada nos documentos.'"},
        {"role": "user", "content": f"Document:\n{context_text}"},
        {"role": "user", "content": f"Question: {user_question}"}
    ]

    response = openai.chat.completions.create(
    model="gpt-4o",
    messages=prompt,
    max_tokens=300,
    temperature=0
    )

    answer = response.choices[0].message.content.strip()
    return jsonify({"response_type": "in_channel", "text": answer})

@app.route('/ask', methods=['GET', 'POST'])
def ask():
    answer = None
    if request.method == 'POST':
        user_question = request.form.get('question')
        global index, texts
        if index is None or len(texts) == 0:
            answer = "A base de conhecimento está vazia. O administrador deve fazer upload de PDFs primeiro."
        else:
            context_chunks = search_index(user_question, index, texts, top_k=3)
            context_text = "\n\n".join(context_chunks)
            prompt = [
                {"role": "system", "content": "Você responde perguntas baseadas apenas no documentos providenciados. Procure e leia atentamente cada documento para que uma pergunta simples não passe despercebida. Se não for possível achar a resposta, simplesmente responda 'Informação não encontrada nos documentos.'"},
                {"role": "user", "content": f"Document:\n{context_text}"},
                {"role": "user", "content": f"Question: {user_question}"}
            ]
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=prompt,
                max_tokens=300,
                temperature=0
            )
            answer = response.choices[0].message.content.strip()
    return render_template_string("""
        <h2>Faça uma pergunta sobre os PDFs</h2>
        <form method="post">
            <input type="text" name="question" placeholder="Digite sua pergunta" required/>
            <button type="submit">Perguntar</button>
        </form>
        {% if answer %}
            <h3>Resposta:</h3>
            <div style="border:1px solid #ccc;padding:10px;">{{ answer }}</div>
        {% endif %}
        """, answer=answer)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    index = load_faiss_index()
    texts = load_texts()
    app.run(host='0.0.0.0', port=port)
# Dockerfile untuk deploy backend ke Hugging Face Spaces (SDK: docker).
# Mengikuti pola resmi HF: berjalan sebagai user non-root, listen di port 7860.
FROM python:3.11

# User non-root sesuai rekomendasi HF Spaces
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/home/user/.cache/hf \
    HUGGINGFACE_HUB_CACHE=/home/user/.cache/hf \
    TRANSFORMERS_CACHE=/home/user/.cache/hf \
    MEDCHATBOT_ROOT=/home/user/app

WORKDIR /home/user/app

RUN pip install --no-cache-dir --upgrade pip
# PyTorch versi CPU (di Linux, default "pip install torch" menarik build CUDA ~2GB).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kode aplikasi + artefak model (folder outputs/ ada di root repo Space).
COPY --chown=user app/ ./app/
COPY --chown=user outputs/ ./outputs/

EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]

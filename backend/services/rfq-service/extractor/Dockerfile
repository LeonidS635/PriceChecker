FROM python:3.12-slim

# PyTorch wheel: cpu (default) or cuda (set RFQ_GLINER_DEVICE=cuda in .env)
ARG DEVICE=cpu

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Pin HuggingFace cache to a predictable path inside the image so the
# weights baked at build time are found at runtime without network access.
ENV HF_HOME=/app/.cache/huggingface

WORKDIR /app

# LibreOffice (soffice) for legacy .doc / .xls conversion
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libreoffice-writer \
        libreoffice-calc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install PyTorch before the rest of the requirements.
RUN if [ "$RFQ_GLINER_DEVICE" = "cuda" ]; then \
      pip install --no-cache-dir torch; \
    else \
      pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu; \
    fi

RUN pip install --no-cache-dir -r requirements.txt

# Bake GLiNER weights into the image.
RUN python -c "from gliner import GLiNER; GLiNER.from_pretrained('urchade/gliner_multi-v2.1')"

COPY extractor ./extractor

CMD ["python", "-m", "extractor"]

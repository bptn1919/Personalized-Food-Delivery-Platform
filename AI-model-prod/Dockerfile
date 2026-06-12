FROM python:3.11-slim  

WORKDIR /app

ENV HF_HUB_DISABLE_XET=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api.py predict.py config.py rule_engine.py rule_config.json phobert_model.py ./

EXPOSE 8001

CMD ["python", "api.py"]
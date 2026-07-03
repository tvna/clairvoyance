# Throwaway E2E fixture image (design doc §13) -- standalone from
# managed/pyproject.toml on purpose, so the real backend's dependency
# tree never sees this.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./
EXPOSE 8000
CMD ["python", "app.py"]

# 1. Base image
FROM python:3.10-slim

# 2. Working directory
WORKDIR /app

# 3. Copy all files
COPY . .

# 4. Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 5. Expose port
EXPOSE 5000

# 6. Run the app
CMD ["python", "app.py"]

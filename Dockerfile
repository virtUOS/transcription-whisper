FROM python:3.12-slim
EXPOSE 8501

# Install debian packages
RUN apt-get update && apt-get install -y \
    ffmpeg

# Install dependencies
COPY requirements.txt /kiwi/requirements.txt
RUN pip install --no-cache-dir -r /kiwi/requirements.txt

# Copy the current directory contents into the container at /app
COPY . /kiwi
WORKDIR /kiwi

# Create non-root user for security
RUN useradd -s /bin/bash streamlituser

# Healthcheck to ensure the app is running
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the Streamlit app
ENTRYPOINT ["./entrypoint.sh"]

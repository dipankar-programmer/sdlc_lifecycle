FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements from root context (build context = hackathon/)
COPY requirements_base.txt .
COPY requirements.txt .

# Install base and then full requirements
RUN pip install --no-cache-dir -r requirements_base.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY src/software_life_cycle /app
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Default command
CMD ["python", "main.py"]

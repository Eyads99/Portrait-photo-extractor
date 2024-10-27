FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000
# Command to run your Python script
CMD ["python", "/app/api.py"]
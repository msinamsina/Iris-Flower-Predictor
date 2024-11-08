# Use an official Python runtime as a base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install the required dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the Flask app's default port
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]

ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . .
RUN mkdir /persistent  # Create new folder inside for log and database.
RUN chown -R 1000:1000 /persistent  # Change it's permissions to allow writing.

RUN python -m pip install -r requirements.txt  # Install dependencies

# Expose the port that the application listens on.
EXPOSE 49153

# Run the application.
CMD ./server.py

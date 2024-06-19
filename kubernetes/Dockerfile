FROM python:3.11

# Setup working directory
WORKDIR /app

# Run the webapp
COPY . .
RUN pip install -r requirements.txt
EXPOSE 2138
CMD [  "/bin/bash",\
       "wait-for-it/wait-for-it.sh", "localhost:6379", "--timeout=20", "--strict",\
       "--",\
       "python", "-m", "uvicorn", "main:app" , "--port=2138"\
]
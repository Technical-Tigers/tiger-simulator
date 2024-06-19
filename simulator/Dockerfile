FROM python:3.11

# Setup working directory
WORKDIR /app

# Run the webapp
COPY . .
RUN pip install -r requirements.txt
EXPOSE 2137
CMD [ "/bin/bash", \
      "wait-for-it/wait-for-it.sh", "localhost:7270", "--timeout=20","--strict",\
      "--",\
      "python",  "main.py", "--log=INFO"\
]

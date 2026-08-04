# define language/framework
FROM python:3.12-slim

# set working directory in container
WORKDIR /backend

# copy requirements.txt into working directory
COPY requirements.txt .

# install dependencies without caching
RUN pip install --no-cache-dir -r requirements.txt

# copy everything in current directory into working directory (besides ignore)
COPY . .

# expose the port, then run the command to start the server
EXPOSE 8000
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
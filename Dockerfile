#Use small python alpine base
FROM python:3.13-alpine

#install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

#copy rest of the code
COPY . .

#Run application
ENTRYPOINT ["python", "main.py"]
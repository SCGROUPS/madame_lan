FROM python:3.8-bullseye

WORKDIR /app/backend

COPY ./backend/ /app/backend/
# COPY ./frontend/ /app/frontend/

RUN pip install -r requirements.txt

# RUN apt-get update && \
#     apt-get -y install npm && \
#     curl -s https://deb.nodesource.com/setup_20.x | bash && \
#     apt-get -y install nodejs && \
#     npm install -g vite yarn && \
#     apt-get install -y bash dos2unix

# RUN dos2unix /app/backend/deploy/start_build_frontend.sh

# RUN chmod +x /app/backend/deploy/start_build_frontend.sh

# RUN /bin/bash /app/backend/deploy/start_build_frontend.sh

EXPOSE 5000

CMD ["uvicorn", "main:app", "--port=3000", "--host=0.0.0.0"]
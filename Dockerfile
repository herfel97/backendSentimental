# Imagen base para la aplicación Flask
FROM python:3.10.11
COPY . /backend_analisis_de_sentimientos
WORKDIR /backend_analisis_de_sentimientos
RUN pip install --upgrade pip
RUN pip cache purge
RUN pip install -r requeriments.txt
EXPOSE 5001
CMD ["python", "-u", "principal.py"]

build:
	docker build -t app-django .

run: build
	docker run -v ./data_app/migrations:/app/data_app/migrations --name app-django -p 8234:8234 -p 8085:8085 --rm -it app-django

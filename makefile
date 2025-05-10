build:
	docker build -t app-django .

run: build
	docker run \
		-v ./data_app/migrations:/app/data_app/migrations \
		-v ./raw_data/migrations:/app/raw_data/migrations \
		--name app-django \
		-p 8234:8234 \
		-p 8085:8085 \
		-p 8086:8086 \
		--rm -it app-django

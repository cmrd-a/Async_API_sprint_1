black:
	black . --line-length 120

dbs:
	docker compose up postgres redis elastic -d
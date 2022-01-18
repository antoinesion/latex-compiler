update:
	git fetch
	git pull

deploy:
ifneq ($(shell sudo docker ps -q),)
	$(info Stopping all containers...)
	sudo docker stop $(shell sudo docker ps -q)
endif
	sudo fn deploy --verbose --create-app --local --no-bump $(NAME)
	echo "Pruning docker resources..."
	sudo docker system prune -f

deploy-all:
ifneq ($(shell sudo docker ps -q),)
	$(info Stopping all containers...)
	sudo docker stop $(shell sudo docker ps -q)
endif
	sudo fn deploy --verbose --create-app --all --local --no-bump
	echo "Pruning docker resources..."
	sudo docker system prune -f

# Do not forget protocol in URL (e.g. tcp+tls://...)
send-logs:
	sudo fn update app compile-latex --syslog-url=$(URL)
update:
	git fetch
	git pull

deploy:
	sudo fn deploy --verbose --create-app --local --no-bump $(NAME)
ifneq ($(shell sudo docker ps -q),)
	$(info Stopping all containers...)
	sudo docker stop $(shell sudo docker ps -q)
endif
	echo "Pruning docker resources..."
	sudo docker system prune -f

deploy-all:
	sudo fn deploy --verbose --create-app --all --local --no-bump
ifneq ($(shell sudo docker ps -q),)
	$(info Stopping all containers...)
	sudo docker stop $(shell sudo docker ps -q)
endif
	echo "Pruning docker resources..."
	sudo docker system prune -f

# Do not forget protocol in URL (e.g. tcp+tls://...)
send-logs:
	sudo fn update app compile-latex --syslog-url=$(URL)
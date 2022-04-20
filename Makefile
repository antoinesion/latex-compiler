update:
	git fetch
	git pull

build-docker:
	sudo docker build -t latex-compiler-base docker/

deploy:
	sudo fn deploy --verbose --create-app --local --no-bump $(NAME)
ifneq ($(shell sudo docker ps -q),)
	sudo docker stop $(shell sudo docker ps -q)
endif
	sudo docker system prune -f

deploy-all:
	sudo fn deploy --verbose --create-app --all --local --no-bump
ifneq ($(shell sudo docker ps -q),)
	sudo docker stop $(shell sudo docker ps -q)
endif
	sudo docker system prune -f

follow-logs:
	journalctl -f -u fnserver
# Do not forget protocol in URL (e.g. tcp+tls://...)
send-logs:
	sudo fn update app compile --syslog-url=$(URL)
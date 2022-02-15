# LaTeX Compiler Using Fn Project

## Steps

1. [Download Ubuntu Server](https://ubuntu.com/download/server)
2. [Create a bootable USB (Windows here)](https://ubuntu.com/tutorials/create-a-usb-stick-on-windows)
3. [Install Ubuntu Server](https://ubuntu.com/tutorials/install-ubuntu-server)
4. [Install Docker](https://docs.docker.com/engine/install/ubuntu) (this step can be achieved in the previous one)
5. [Install Go](https://go.dev/doc/install)
6. [Install Go Dep](https://golang.github.io/dep/docs/installation.html)
7. [Install Fn Server & CLI](https://medium.com/@varpa89/run-fn-project-on-your-raspberry-pi-fa17f5067b47) (Step 2. & 3.)
8. Clone this repo: `git clone https://github.com/antoinesion/latex-compiler.git`
9. Build docker base image: `make build-docker`
10. Configure your router: Static local IP & Port Forwarding
11. [Installing No-IP DUC on Ubuntu](https://www.noip.com/support/knowledgebase/installing-the-linux-dynamic-update-client-on-ubuntu/)
12. [Sending function logs to Papertrail](https://medium.com/fnproject/sending-function-logs-to-papertrail-c1ba2bae62e6) \+ `make send-logs`

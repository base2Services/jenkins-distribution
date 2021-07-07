FROM jenkins/jenkins:lts-slim

USER root

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install git-remote-codecommit

USER jenkins

COPY plugins.yaml $REF/plugins.yaml 

RUN jenkins-plugin-cli --plugin-file $REF/plugins.yaml --view-all-security-warnings --latest true --verbose

COPY create-user.groovy $JENKINS_HOME/init.groovy.d/custom.groovy

FROM jenkins/jenkins:2.319.3-jdk11

LABEL org.opencontainers.image.source = https://github.com/base2Services/jenkins-distribution

USER root

COPY requirements.txt $REF/requirements.txt

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install -r $REF/requirements.txt

USER jenkins

COPY plugins.yaml $REF/plugins.yaml

RUN jenkins-plugin-cli --plugin-file $REF/plugins.yaml --view-all-security-warnings --latest true --verbose

COPY init.groovy.d/ $REF/init.groovy.d/

COPY --chown=jenkins:jenkins jcasc/defaults.yaml /cfg/jenkins.yaml
COPY jcasc/defaults.yaml $REF/defaults.yaml
COPY jcasc/default_parameters.yaml $REF/default_parameters.yaml
COPY jcasc/jenkmon.txt $REF/jenkmon.txt

COPY jcasc/jcasc-apply.py /usr/local/bin/jcasc-apply

# so we can run this in code build
VOLUME /var/lib/docker

FROM cloudbees/cloudbees-jenkins-distribution:2.249.2.3

ENV PLUGIN_MANAGER_VERSION=2.1.0
RUN wget -P $REF "https://github.com/jenkinsci/plugin-installation-manager-tool/releases/download/$PLUGIN_MANAGER_VERSION/jenkins-plugin-manager-$PLUGIN_MANAGER_VERSION.jar"

ENV JENKINS_UPDATE_CENTER=https://jenkins-updates.cloudbees.com/update-center/cloudbees-jenkins-distribution/update-center.json
ENV JENKINS_EXPERIMENTAL_UPDATE_CENTER=https://jenkins-updates.cloudbees.com/update-center/experimental/update-center.json

COPY plugins.yaml $REF/plugins.yaml 

RUN java -jar $REF/jenkins-plugin-manager-$PLUGIN_MANAGER_VERSION.jar\
        --jenkins-update-center $JENKINS_UPDATE_CENTER \
        --jenkins-experimental-update-center $JENKINS_EXPERIMENTAL_UPDATE_CENTER \
        --plugin-download-directory $REF/plugins \
        --plugin-file $REF/plugins.yaml \
        --war $JENKINS_WAR \
        --view-all-security-warnings \
        --latest false \
        --verbose 

COPY create-user.groovy $JENKINS_HOME/init.groovy.d/custom.groovy
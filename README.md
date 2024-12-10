# Jenkins Distribution for CI in a Box 2.0

This project provides a customized Jenkins distribution for CI in a Box 2.0, offering a pre-configured Jenkins environment with essential plugins and configurations.

The distribution is designed to streamline the setup process for continuous integration and delivery pipelines, particularly for AWS-based infrastructures. It includes a comprehensive set of plugins for source control management, build automation, cloud integration, and security features.

Key features of this Jenkins distribution include:
- Pre-installed plugins for AWS, Docker, and various SCM systems
- Configuration as Code (JCasC) for easy setup and maintenance
- Integration with ciinabox-specific components
- Customizable job configurations and build strategies
- Support for cloud-based agent provisioning

## Repository Structure

- `Dockerfile`: Defines the custom Jenkins image build
- `docker-compose.yaml`: Configures the local development environment
- `jcasc.yaml`: Jenkins Configuration as Code file
- `plugins.yaml`: List of plugins to be installed
- `init.groovy.d/`: Contains initialization scripts
- `jcasc/`: Directory for JCasC related files
  - `defaults.yaml`: Default Jenkins configuration
  - `jcasc-apply.py`: Script to apply JCasC configurations
  - `plugin-merger.py`: Script to merge plugin configurations
- `README.md`: This file, containing project documentation

## Usage Instructions

### Installation

Prerequisites:
- Docker and Docker Compose installed (version 19.03.0+)
- Git

Steps:
1. Clone the repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Build and start the Jenkins container:
   ```
   docker-compose up --build
   ```

3. Access Jenkins at `http://localhost:8080`

### Configuration

The Jenkins instance is pre-configured using Jenkins Configuration as Code (JCasC). The main configuration file is `jcasc/defaults.yaml`. To customize the configuration:

1. Modify the `jcasc/defaults.yaml` file
2. Apply changes using the `jcasc-apply.py` script:
   ```
   python3 jcasc/jcasc-apply.py --jcasc-yaml jcasc/defaults.yaml
   ```

### Adding or Updating Plugins

To add or update plugins:

1. Edit the `plugins.yaml` file
2. Rebuild the Docker image:
   ```
   docker-compose build
   ```
3. Restart the Jenkins container:
   ```
   docker-compose up -d
   ```

### Customizing Job Configurations

Job configurations can be customized using the Job DSL plugin. Add or modify job definitions in the `jcasc/ciinabox-jobs` directory.

### Troubleshooting

1. Jenkins fails to start:
   - Check Docker logs: `docker-compose logs jenkins`
   - Verify JCasC configuration in `jcasc/defaults.yaml`
   - Ensure all required environment variables are set in `docker-compose.yaml`

2. Plugin compatibility issues:
   - Review `plugins.yaml` for version conflicts
   - Check Jenkins system logs for plugin-related errors
   - Try updating problematic plugins to their latest versions

3. Configuration changes not applying:
   - Ensure you've run the `jcasc-apply.py` script after making changes
   - Verify the JCASC_RELOAD_TOKEN is correctly set in the environment
   - Check Jenkins logs for JCasC-related messages

4. AWS integration issues:
   - Verify AWS credentials are correctly configured in Jenkins
   - Check EC2 plugin configuration in `jcasc/defaults.yaml`
   - Ensure proper IAM permissions for the Jenkins instance

For more detailed debugging:
- Enable Jenkins debug logging by adding `-Djava.util.logging.config.file=/var/jenkins_home/log.properties` to JAVA_OPTS in `docker-compose.yaml`
- Inspect logs at `/var/jenkins_home/jenkins.log` inside the container

## Data Flow

The Jenkins distribution follows this general data flow for job execution:

1. User triggers a job or SCM webhook initiates a build
2. Jenkins master receives the build request
3. If using cloud agents, Jenkins provisions an EC2 instance via the EC2 plugin
4. Job configuration is loaded from JCasC or Job DSL definitions
5. Build steps are executed on the agent (or master for lightweight jobs)
6. Build artifacts are stored (locally or in S3, depending on configuration)
7. Build results are reported back to the Jenkins master
8. Notifications are sent based on build status (email, Slack, etc.)

```
[User/SCM] -> [Jenkins Master] -> [EC2 Plugin] -> [EC2 Agent]
                  |                                  |
                  v                                  v
           [Job Configuration] -----------------> [Build Execution]
                  |                                  |
                  v                                  v
           [Artifact Storage] <----------------- [Build Results]
                  |
                  v
         [Notifications/Reporting]
```

## Infrastructure

The infrastructure for this Jenkins distribution is primarily defined in the `Dockerfile` and `docker-compose.yaml` files. Key components include:

- Docker:
  - `Dockerfile`: Defines the custom Jenkins image based on `jenkins/jenkins:2.479.2-jdk17`
  - `docker-compose.yaml`: Configures the Jenkins service for local development

- Jenkins:
  - Exposed ports: 8080 (web interface), 50000 (agent communication)
  - Volume mounts:
    - `/var/run/docker.sock`: Allows Jenkins to interact with the Docker daemon
    - `./jcasc.yaml`: Mounts the JCasC configuration file

- Environment variables:
  - `CASC_JENKINS_CONFIG`: Specifies the location of the JCasC configuration
  - `TRY_UPGRADE_IF_NO_MARKER`: Enables automatic plugin upgrades
  - `PLUGINS_FORCE_UPGRADE`: Forces plugin upgrades
  - `JCASC_RELOAD_TOKEN`: Token for reloading JCasC configuration
  - `JAVA_OPTS`: Various Java options for Jenkins, including security settings

- AWS (configured in `jcasc/defaults.yaml`):
  - EC2 plugin configuration for provisioning cloud agents
  - IAM instance profile (not specified in provided files)
  - Security groups and subnets for EC2 instances

Note: Specific AWS resource identifiers (e.g., AMI IDs, security group IDs) are placeholders in the provided configuration and should be replaced with actual values for production use.
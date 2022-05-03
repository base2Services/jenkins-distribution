pipelineJob('monitoring/jenkMon-agent-monitor-{{LABEL}}') {
    properties {
        pipelineTriggers {
            triggers {
                cron {
                    spec('{{CRON}}')
                }
            }
        }
    }
    definition {
        cps {
            script('''
                @Library(['ciinabox']) _
                jenkMon {
                    checkDocker = '{{CHECK_DOCKER}}'
                    agentLabel = '{{LABEL}}'
                }
            '''.stripIndent())
            sandbox()
        }
    }
}
pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS_ID = 'cbf5d4be-0b0d-499a-a184-196c2d80cf2b'
        DOCKER_IMAGE = 'jeromejoseph/pentest-orchestrator'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // stage('Run Tests') {
        //     steps {
        //         sh 'pytest tests/'
        //     }
        // }

        stage('Build Docker Image') {
            steps {
                script {
                    dockerImage = docker.build("${DOCKER_IMAGE}:${env.BRANCH_NAME}")
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry('', DOCKER_CREDENTIALS_ID) {
                        dockerImage.push("${env.BRANCH_NAME}")
                        if (env.BRANCH_NAME == 'main') {
                            dockerImage.push('latest')
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            sh "docker rmi ${DOCKER_IMAGE}:${env.BRANCH_NAME} || true"
            sh "docker rmi ${DOCKER_IMAGE}:latest || true"
        }
        failure {
            echo 'Build failed. Please check the logs for details.'
        }
    }
}

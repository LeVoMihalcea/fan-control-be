pipeline{
    agent any

    stages {
        stage('Waking up'){
            steps{
                echo 'Waking up'
            }
        }

        stage('Taking down the old container'){
            steps{
                sh "docker compose -f ./docker-compose.yml down || docker-compose -f ./docker-compose.yml down || true"
            }
        }

        stage('Removing old Docker image'){
            steps{
                sh "docker image rm fan-control-bt || true"
            }
        }

        stage('Building new Docker Image'){
            steps{
                sh "docker build -t fan-control-bt ."
            }
        }

        stage('Starting up new Container'){
            steps{
                sh "docker compose -f ./docker-compose.yml up -d || docker-compose -f ./docker-compose.yml up -d"
            }
        }
    }

    post{ always { echo 'Build completed' } }
}

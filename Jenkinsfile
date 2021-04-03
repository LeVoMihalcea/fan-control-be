pipeline{
    agent any

    stages {
        stage('Deployment'){
            steps{
                sh '''
                        docker-compose -f /opt/fan-control-be/docker-compose.yml down || true
                        docker image rm fan-control-be || true
                        docker build -t fan-control-be .
                        docker-compose -f /opt/fan-control-be/docker-compose.yml up -dt
                '''
            }
        }
    }
}

pipeline {

    agent any

    environment {

        AWS_REGION = 'ap-south-1'

        BACKEND_REPOSITORY = 'vcp-backend'

        FRONTEND_REPOSITORY = 'vcp-frontend'

        APP_SERVER = '10.0.1.24'
    }


    options {

        timestamps()

        disableConcurrentBuilds()
    }


    stages {


        stage('Checkout') {

            steps {

                echo 'Checking out source code'

                checkout scm

                sh '''
                    echo "Git Commit:"
                    git rev-parse HEAD

                    echo "Branch:"
                    git branch --show-current
                '''
            }
        }


        stage('Set Build Variables') {

            steps {

                script {

                    env.AWS_ACCOUNT_ID = sh(
                        script: '''
                            aws sts get-caller-identity \
                            --query Account \
                            --output text
                        ''',
                        returnStdout: true
                    ).trim()


                    env.GIT_SHA = sh(
                        script: '''
                            git rev-parse --short HEAD
                        ''',
                        returnStdout: true
                    ).trim()


                    env.ECR_REGISTRY =
                        "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"


                    env.BACKEND_IMAGE =
                        "${ECR_REGISTRY}/${BACKEND_REPOSITORY}:${GIT_SHA}"


                    env.FRONTEND_IMAGE =
                        "${ECR_REGISTRY}/${FRONTEND_REPOSITORY}:${GIT_SHA}"


                    echo "AWS Account: ${AWS_ACCOUNT_ID}"

                    echo "Version: ${GIT_SHA}"
                }
            }
        }


        stage('Backend Test') {

            steps {

                dir('backend') {

                    sh '''
                        docker run --rm \
                        -v "$PWD:/app" \
                        -w /app \
                         -e PYTHONPATH=/app \
                        python:3.12-slim \
                        sh -c "
                            pip install --no-cache-dir \
                            -r requirements.txt &&
                            pytest -q
                        "
                    '''
                }
            }
        }


        stage('Docker Build') {

            steps {

                echo 'Building backend image'

                sh '''
                    docker build \
                    -t ${BACKEND_IMAGE} \
                    ./backend
                '''


                echo 'Building frontend image'

                sh '''
                    docker build \
                    -t ${FRONTEND_IMAGE} \
                    ./frontend
                '''
            }
        }


        stage('ECR Login') {

            steps {

                sh '''
                    aws ecr get-login-password \
                    --region ${AWS_REGION} \
                    | docker login \
                    --username AWS \
                    --password-stdin \
                    ${ECR_REGISTRY}
                '''
            }
        }


        stage('Push Backend Image') {

            steps {

                sh '''
                    docker push ${BACKEND_IMAGE}

                    docker tag \
                    ${BACKEND_IMAGE} \
                    ${ECR_REGISTRY}/${BACKEND_REPOSITORY}:latest

                    docker push \
                    ${ECR_REGISTRY}/${BACKEND_REPOSITORY}:latest
                '''
            }
        }


        stage('Push Frontend Image') {

            steps {

                sh '''
                    docker push ${FRONTEND_IMAGE}

                    docker tag \
                    ${FRONTEND_IMAGE} \
                    ${ECR_REGISTRY}/${FRONTEND_REPOSITORY}:latest

                    docker push \
                    ${ECR_REGISTRY}/${FRONTEND_REPOSITORY}:latest
                '''
            }
        }


        stage('Deploy to EC2') {

            steps {

                sshagent(
                    credentials: ['app-ec2-ssh-key']
                ) {

                    sh '''
                    ssh \
                    -o StrictHostKeyChecking=no \
                    ubuntu@${APP_SERVER} "

                        set -e

                        echo 'Logging into ECR'

                        aws ecr get-login-password \
                        --region ${AWS_REGION} \
                        | docker login \
                        --username AWS \
                        --password-stdin \
                        ${ECR_REGISTRY}


                        echo 'Pull backend'

                        docker pull \
                        ${BACKEND_IMAGE}


                        echo 'Pull frontend'

                        docker pull \
                        ${FRONTEND_IMAGE}


                        echo 'Create Docker network'

                        docker network inspect \
                        virtual-classroom-net \
                        >/dev/null 2>&1 \
                        || docker network create \
                        virtual-classroom-net


                        echo 'Remove old frontend'

                        docker rm -f frontend \
                        || true


                        echo 'Remove old backend'

                        docker rm -f backend \
                        || true


                        echo 'Start backend'

                        docker run -d \
                        --name backend \
                        --restart unless-stopped \
                        --network virtual-classroom-net \
                        --env-file \
                        /opt/virtual-classroom/app.env \
                        --log-driver=awslogs \
                        --log-opt \
                        awslogs-region=${AWS_REGION} \
                        --log-opt \
                        awslogs-group=/vcp/backend \
                        --log-opt \
                        awslogs-create-group=true \
                        ${BACKEND_IMAGE}


                        echo 'Start frontend'

                        docker run -d \
                        --name frontend \
                        --restart unless-stopped \
                        --network virtual-classroom-net \
                        -p 80:80 \
                        --log-driver=awslogs \
                        --log-opt \
                        awslogs-region=${AWS_REGION} \
                        --log-opt \
                        awslogs-group=/vcp/frontend \
                        --log-opt \
                        awslogs-create-group=true \
                        ${FRONTEND_IMAGE}


                        docker ps
                    "
                    '''
                }
            }
        }

    stage('Health Check') {
        steps {
            sshagent(credentials: ['app-ec2-ssh-key']) {
                script {
                    sleep 10

                def status = sh(
                    script: '''
                        ssh -o StrictHostKeyChecking=no ubuntu@10.0.1.24 \
                        "curl -fsS http://localhost/health"
                    ''',
                    returnStatus: true
                )

                if (status != 0) {
                    error('Application health check failed')
                }
            }
        }
    }
}

        stage('Deployment Information') {

            steps {

                echo """
                =======================================
                DEPLOYMENT SUCCESSFUL
                =======================================

                Version:
                ${GIT_SHA}

                Backend:
                ${BACKEND_IMAGE}

                Frontend:
                ${FRONTEND_IMAGE}

                =======================================
                """
            }
        }
    }


    post {


        success {

            echo '''
            =====================================
            VIRTUAL CLASSROOM DEPLOYED SUCCESSFULLY
            =====================================
            '''
        }


        failure {

            echo '''
            =====================================
            DEPLOYMENT FAILED
            Check Jenkins console output.
            =====================================
            '''
        }


        always {

            sh '''
                docker image prune -f || true
            '''
        }
    }
}

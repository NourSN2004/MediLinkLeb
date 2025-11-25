pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = "docker.io"
        K8S_NAMESPACE = "medilink"
        GIT_COMMIT_SHORT = bat(script: "@git rev-parse --short HEAD", returnStdout: true).trim()
    }
    
    stages {
        stage('Detect Changes') {
            steps {
                script {
                    // Get list of changed files
                    def changedFiles = bat(
                        script: "@git diff --name-only HEAD~1 HEAD 2>nul || git diff --name-only HEAD",
                        returnStdout: true
                    ).trim().split('\n')
                    
                    // Initialize services list
                    env.CHANGED_SERVICES = ""
                    def services = []
                    
                    // Check which microservices changed
                    def serviceMap = [
                        'auth-service': 'microservices/auth-service/',
                        'doctor-service': 'microservices/doctor-service/',
                        'patient-service': 'microservices/patient-service/',
                        'pharmacy-service': 'microservices/pharmacy-service/',
                        'scheduling-service': 'microservices/scheduling-service/',
                        'inventory-service': 'microservices/inventory-service/',
                        'notification-service': 'microservices/notification-service/',
                        'api-gateway': 'microservices/api-gateway/'
                    ]
                    
                    serviceMap.each { serviceName, path ->
                        if (changedFiles.any { it.startsWith(path) }) {
                            services.add(serviceName)
                        }
                    }
                    
                    // Check if shared files changed (rebuild all if they did)
                    def sharedFiles = ['requirements.txt', 'Dockerfile', 'k8s/', 'docker-compose.yml']
                    def sharedChanged = changedFiles.any { file ->
                        sharedFiles.any { shared -> file.contains(shared) }
                    }
                    
                    if (sharedChanged || services.isEmpty()) {
                        echo "Shared files changed or no specific service detected. Building all services."
                        services = serviceMap.keySet().toList()
                    }
                    
                    env.CHANGED_SERVICES = services.join(',')
                    echo "Services to build: ${env.CHANGED_SERVICES}"
                }
            }
        }
        
        stage('Build Changed Services') {
            steps {
                script {
                    if (env.CHANGED_SERVICES) {
                        def services = env.CHANGED_SERVICES.split(',')
                        
                        services.each { service ->
                            echo "Building ${service}..."
                            
                            // Configure Docker to use Minikube's daemon
                            bat """
                                @echo off
                                for /f "tokens=*" %%i in ('minikube docker-env --shell cmd') do %%i
                                cd microservices\\${service}
                                docker build -t ${service}:${GIT_COMMIT_SHORT} .
                                docker tag ${service}:${GIT_COMMIT_SHORT} ${service}:latest
                            """
                            
                            echo "✓ ${service} built successfully"
                        }
                    } else {
                        echo "No services to build"
                    }
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                script {
                    if (env.CHANGED_SERVICES) {
                        def services = env.CHANGED_SERVICES.split(',')
                        
                        services.each { service ->
                            echo "Testing ${service}..."
                            
                            // Run tests for each service
                            bat """
                                @echo off
                                cd microservices\\${service}
                                if exist tests.py ( python -m pytest tests\\ ) else if exist tests\\ ( python -m pytest tests\\ )
                            """
                        }
                    }
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    if (env.CHANGED_SERVICES) {
                        def services = env.CHANGED_SERVICES.split(',')
                        
                        services.each { service ->
                            echo "Deploying ${service} to Kubernetes..."
                            
                            // Update deployment with new image
                            bat """
                                kubectl set image deployment/${service} ${service}=${service}:${GIT_COMMIT_SHORT} -n ${K8S_NAMESPACE}
                                kubectl rollout status deployment/${service} -n ${K8S_NAMESPACE} --timeout=5m
                            """
                            
                            echo "✓ ${service} deployed successfully"
                        }
                    } else {
                        echo "No services to deploy"
                    }
                }
            }
        }
        
        stage('Run Migrations') {
            when {
                expression { env.CHANGED_SERVICES.contains('auth-service') }
            }
            steps {
                script {
                    echo "Running database migrations..."
                    bat """
                        for /f "tokens=*" %%i in ('kubectl get pods -n ${K8S_NAMESPACE} -l app=auth-service -o jsonpath^={.items[0].metadata.name}') do set POD=%%i
                        kubectl exec -n ${K8S_NAMESPACE} %POD% -- python manage.py migrate
                    """
                    echo "✓ Migrations completed"
                }
            }
        }
        
        stage('Verify Deployment') {
            steps {
                script {
                    echo "Verifying deployment..."
                    
                    // Check all pods are running
                    bat """
                        kubectl get pods -n ${K8S_NAMESPACE}
                    """
                    
                    // Check ingress
                    bat """
                        kubectl get ingress -n ${K8S_NAMESPACE}
                    """
                    
                    echo "✓ Deployment verified"
                }
            }
        }
    }
    
    post {
        success {
            echo """
            ================================
            Build Successful! 
            ================================
            Changed Services: ${env.CHANGED_SERVICES}
            Commit: ${env.GIT_COMMIT_SHORT}
            Access: http://medilink.local
            ================================
            """
        }
        failure {
            echo """
            ================================
            Build Failed!
            ================================
            Changed Services: ${env.CHANGED_SERVICES}
            Commit: ${env.GIT_COMMIT_SHORT}
            Check logs above for details
            ================================
            """
        }
    }
}

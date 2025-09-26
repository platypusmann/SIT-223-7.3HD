# Additional Jenkins Container Setup (Alternative to Windows Service)
# If you prefer running Jenkins in Docker

Write-Host "Jenkins Docker Setup Alternative" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor White

# 1. Create Jenkins Docker volume for persistence
Write-Host "Creating Jenkins Docker volume..." -ForegroundColor Yellow
docker volume create jenkins_home

# 2. Create network for Jenkins and application
Write-Host "Creating Docker network..." -ForegroundColor Yellow
docker network create jenkins-network

# 3. Run Jenkins with Docker access
Write-Host "Starting Jenkins in Docker..." -ForegroundColor Yellow
$jenkinsCommand = @"
docker run -d \
  --name jenkins-sit223 \
  --restart=unless-stopped \
  --network jenkins-network \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/bin/docker:/usr/bin/docker \
  jenkins/jenkins:lts
"@

Invoke-Expression $jenkinsCommand

Write-Host "Jenkins starting in Docker..." -ForegroundColor Green
Write-Host "Access at: http://localhost:8080" -ForegroundColor White
Write-Host "Initial admin password:" -ForegroundColor Yellow

# Wait for Jenkins to start and show initial password
Start-Sleep -Seconds 30
docker exec jenkins-sit223 cat /var/jenkins_home/secrets/initialAdminPassword

Write-Host "`nJenkins Docker Management Commands:" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor White
Write-Host "View logs: docker logs jenkins-sit223" -ForegroundColor White
Write-Host "Stop: docker stop jenkins-sit223" -ForegroundColor White
Write-Host "Start: docker start jenkins-sit223" -ForegroundColor White
Write-Host "Remove: docker rm jenkins-sit223" -ForegroundColor White
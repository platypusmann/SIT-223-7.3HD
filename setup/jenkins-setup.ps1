# Jenkins Host Setup Commands for Windows
# Run these commands in PowerShell as Administrator

# =============================================================================
# JENKINS SETUP FOR SIT223 Task 7.3HD
# =============================================================================

Write-Host "Setting up Jenkins environment for SIT223 Task 7.3HD..." -ForegroundColor Green

# 1. Install Python 3.11
Write-Host "Installing Python 3.11..." -ForegroundColor Yellow
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    # Download and install Python 3.11
    $pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
    $pythonInstaller = "$env:TEMP\python-3.11.7-amd64.exe"
    
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller
    Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0" -Wait
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Write-Host "Python installed successfully" -ForegroundColor Green
} else {
    Write-Host "Python already installed: $(python --version)" -ForegroundColor Green
}

# 2. Ensure pip is available and upgrade it
Write-Host "Setting up pip..." -ForegroundColor Yellow
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel

# 3. Install Docker Desktop for Windows
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker not found. Please install Docker Desktop from: https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor Red
    Write-Host "After installing Docker Desktop:" -ForegroundColor Yellow
    Write-Host "1. Enable WSL 2 backend" -ForegroundColor White
    Write-Host "2. Start Docker Desktop" -ForegroundColor White
    Write-Host "3. Verify with: docker --version" -ForegroundColor White
} else {
    Write-Host "Docker already installed: $(docker --version)" -ForegroundColor Green
}

# 4. Install Jenkins (if not already installed)
Write-Host "Jenkins installation info..." -ForegroundColor Yellow
Write-Host "If Jenkins is not installed, download from: https://www.jenkins.io/download/" -ForegroundColor White
Write-Host "Recommended: Install Jenkins as Windows service" -ForegroundColor White

# 5. Install Git (if not already installed)
Write-Host "Checking Git installation..." -ForegroundColor Yellow
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git not found. Installing Git..." -ForegroundColor Yellow
    
    # Install Git using winget (Windows 10/11)
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Git.Git -e --source winget
    } else {
        Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Red
    }
} else {
    Write-Host "Git already installed: $(git --version)" -ForegroundColor Green
}

# 6. Install additional tools for Jenkins pipeline
Write-Host "Installing additional pipeline tools..." -ForegroundColor Yellow

# Install curl (usually comes with Windows 10+)
if (!(Get-Command curl -ErrorAction SilentlyContinue)) {
    Write-Host "Installing curl..." -ForegroundColor Yellow
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id curl.curl
    }
}

# 7. Jenkins Plugin Requirements
Write-Host "`nJenkins Plugins Required:" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor White
Write-Host "1. Docker Pipeline Plugin" -ForegroundColor White
Write-Host "2. Blue Ocean (optional, for better UI)" -ForegroundColor White
Write-Host "3. HTML Publisher Plugin (for coverage reports)" -ForegroundColor White
Write-Host "4. JUnit Plugin (for test reports)" -ForegroundColor White
Write-Host "5. Git Plugin" -ForegroundColor White
Write-Host "6. Pipeline Stage View Plugin" -ForegroundColor White

# 8. Jenkins Configuration Steps
Write-Host "`nJenkins Configuration Steps:" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor White
Write-Host "1. Access Jenkins at: http://localhost:8080" -ForegroundColor White
Write-Host "2. Install suggested plugins" -ForegroundColor White
Write-Host "3. Create admin user" -ForegroundColor White
Write-Host "4. Go to Manage Jenkins > Global Tool Configuration" -ForegroundColor White
Write-Host "5. Configure Python installation" -ForegroundColor White
Write-Host "6. Configure Docker installation" -ForegroundColor White
Write-Host "7. Configure Git installation" -ForegroundColor White

# 9. Create Jenkins Pipeline Job
Write-Host "`nJenkins Pipeline Job Setup:" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor White
Write-Host "1. New Item > Pipeline" -ForegroundColor White
Write-Host "2. Pipeline Definition: Pipeline script from SCM" -ForegroundColor White
Write-Host "3. SCM: Git" -ForegroundColor White
Write-Host "4. Repository URL: <your-github-repo-url>" -ForegroundColor White
Write-Host "5. Script Path: Jenkinsfile" -ForegroundColor White

# 10. Docker Integration with Jenkins
Write-Host "`nDocker Integration:" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor White
Write-Host "1. Ensure Jenkins user has Docker permissions" -ForegroundColor White
Write-Host "2. On Windows, Jenkins should run as Administrator or" -ForegroundColor White
Write-Host "   add Jenkins user to docker-users group" -ForegroundColor White

# 11. Environment Variables for Jenkins
Write-Host "`nEnvironment Variables Setup:" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor White
Write-Host "Add these to Jenkins system configuration:" -ForegroundColor White
Write-Host "PYTHON_PATH: C:\Python311" -ForegroundColor White
Write-Host "DOCKER_PATH: C:\Program Files\Docker\Docker\resources\bin" -ForegroundColor White
Write-Host "GIT_PATH: C:\Program Files\Git\bin" -ForegroundColor White

# 12. Firewall and Network Configuration
Write-Host "`nNetwork Configuration:" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor White
Write-Host "Ensure these ports are accessible:" -ForegroundColor White
Write-Host "- Jenkins: 8080" -ForegroundColor White  
Write-Host "- Application: 8000" -ForegroundColor White
Write-Host "- Docker containers: 8000" -ForegroundColor White

# 13. Security Configuration
Write-Host "`nSecurity Setup:" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor White
Write-Host "1. Enable Jenkins security" -ForegroundColor White
Write-Host "2. Configure user permissions" -ForegroundColor White
Write-Host "3. Set up GitHub webhook (optional)" -ForegroundColor White
Write-Host "4. Configure Docker registry access if needed" -ForegroundColor White

# 14. Verification Commands
Write-Host "`nVerification Commands:" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor White
Write-Host "Run these commands to verify setup:" -ForegroundColor White

$commands = @(
    "python --version",
    "pip --version", 
    "docker --version",
    "docker-compose --version",
    "git --version",
    "curl --version"
)

foreach ($cmd in $commands) {
    Write-Host "Testing: $cmd" -ForegroundColor Yellow
    try {
        $result = Invoke-Expression $cmd
        Write-Host "✓ $result" -ForegroundColor Green
    } catch {
        Write-Host "✗ Failed: $cmd" -ForegroundColor Red
    }
}

# 15. Final Setup Instructions
Write-Host "`nFinal Setup Steps:" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor White
Write-Host "1. Restart Jenkins service after installing tools" -ForegroundColor White
Write-Host "2. Test pipeline with a simple build" -ForegroundColor White
Write-Host "3. Check Jenkins logs for any issues: C:\ProgramData\Jenkins\.jenkins\logs\" -ForegroundColor White
Write-Host "4. Ensure GitHub repository access is configured" -ForegroundColor White

Write-Host "`nSetup Complete! 🎉" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start Jenkins service" -ForegroundColor White
Write-Host "2. Access http://localhost:8080" -ForegroundColor White
Write-Host "3. Create your pipeline job" -ForegroundColor White
Write-Host "4. Run your first build!" -ForegroundColor White

# Optional: Create a Jenkins service restart command
Write-Host "`nJenkins Service Management:" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor White
Write-Host "Restart Jenkins: Restart-Service Jenkins" -ForegroundColor White
Write-Host "Stop Jenkins: Stop-Service Jenkins" -ForegroundColor White
Write-Host "Start Jenkins: Start-Service Jenkins" -ForegroundColor White
Write-Host "Check Status: Get-Service Jenkins" -ForegroundColor White
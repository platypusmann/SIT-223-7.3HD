#!/bin/bash
# Docker Availability Diagnostic Script
# Run this script to check Docker availability for Jenkins

echo "=== DOCKER AVAILABILITY DIAGNOSTIC ==="
echo "Date: $(date)"
echo "User: $(whoami)"
echo "Working Directory: $(pwd)"
echo

# 1. Check current PATH
echo "1. CURRENT PATH:"
echo "PATH: $PATH"
echo

# 2. Search for Docker executables
echo "2. SEARCHING FOR DOCKER EXECUTABLES:"
DOCKER_LOCATIONS="/usr/bin/docker /usr/local/bin/docker /bin/docker /snap/bin/docker"

for location in $DOCKER_LOCATIONS; do
    echo "  Checking: $location"
    if [ -f "$location" ]; then
        echo "    ✅ File exists"
        if [ -x "$location" ]; then
            echo "    ✅ Executable"
            echo "    Version: $($location --version 2>/dev/null || echo 'Cannot get version')"
        else
            echo "    ❌ Not executable"
        fi
    else
        echo "    ❌ File not found"
    fi
done

# 3. Check command -v docker
echo
echo "3. COMMAND -V DOCKER TEST:"
if command -v docker >/dev/null 2>&1; then
    DOCKER_PATH=$(command -v docker)
    echo "✅ Docker found via 'command -v': $DOCKER_PATH"
    echo "Version: $(docker --version 2>/dev/null || echo 'Cannot get version')"
else
    echo "❌ Docker not found via 'command -v'"
fi

# 4. Check which docker
echo
echo "4. WHICH DOCKER TEST:"
if which docker >/dev/null 2>&1; then
    WHICH_DOCKER=$(which docker)
    echo "✅ Docker found via 'which': $WHICH_DOCKER"
else
    echo "❌ Docker not found via 'which'"
fi

# 5. Check Docker daemon
echo
echo "5. DOCKER DAEMON TEST:"
if command -v docker >/dev/null 2>&1; then
    echo "Testing Docker daemon access..."
    if docker info >/dev/null 2>&1; then
        echo "✅ Docker daemon accessible"
        echo "Docker info summary:"
        docker info | head -10 2>/dev/null || echo "Cannot get docker info details"
    else
        echo "❌ Docker daemon not accessible"
        echo "Error output:"
        docker info 2>&1 | head -5 || echo "Cannot get error details"
    fi
else
    echo "❌ Docker command not available for daemon test"
fi

# 6. Check Docker socket
echo
echo "6. DOCKER SOCKET PERMISSIONS:"
if [ -S /var/run/docker.sock ]; then
    echo "✅ Docker socket exists: /var/run/docker.sock"
    echo "Socket permissions:"
    ls -la /var/run/docker.sock
    echo "Socket group info:"
    stat -c "%G %g" /var/run/docker.sock 2>/dev/null || echo "Cannot get group info"
else
    echo "❌ Docker socket not found at /var/run/docker.sock"
    echo "Checking alternative locations:"
    find /var/run -name "*docker*" 2>/dev/null | head -5 || echo "No docker-related files in /var/run"
fi

# 7. Check user groups
echo
echo "7. USER GROUP MEMBERSHIP:"
echo "Current user: $(whoami)"
echo "All groups: $(groups)"
echo "Checking docker group membership:"
if groups | grep -q docker; then
    echo "✅ User is in 'docker' group"
else
    echo "❌ User is NOT in 'docker' group"
fi

# 8. Check Docker service status
echo
echo "8. DOCKER SERVICE STATUS:"
if command -v systemctl >/dev/null 2>&1; then
    echo "Systemctl available, checking Docker service:"
    if systemctl is-active docker >/dev/null 2>&1; then
        echo "✅ Docker service is active"
        systemctl status docker --no-pager -l | head -10 2>/dev/null || echo "Cannot get service details"
    else
        echo "❌ Docker service is not active"
        echo "Service status:"
        systemctl status docker --no-pager | head -5 2>/dev/null || echo "Cannot get status"
    fi
else
    echo "systemctl not available, checking with service command:"
    if command -v service >/dev/null 2>&1; then
        service docker status 2>/dev/null | head -5 || echo "Cannot check service status"
    else
        echo "No service management tools available"
    fi
fi

# 9. Check Docker process
echo
echo "9. DOCKER PROCESS CHECK:"
echo "Docker-related processes:"
ps aux | grep -i docker | grep -v grep | head -5 || echo "No Docker processes found"

# 10. Environment variables
echo
echo "10. DOCKER ENVIRONMENT VARIABLES:"
env | grep -i docker || echo "No Docker-related environment variables"

# 11. Package manager check
echo
echo "11. DOCKER PACKAGE STATUS:"
if command -v dpkg >/dev/null 2>&1; then
    echo "Checking installed Docker packages (Debian/Ubuntu):"
    dpkg -l | grep -i docker | head -5 || echo "No Docker packages found"
elif command -v rpm >/dev/null 2>&1; then
    echo "Checking installed Docker packages (RHEL/CentOS):"
    rpm -qa | grep -i docker | head -5 || echo "No Docker packages found"
else
    echo "No package manager available for check"
fi

echo
echo "=== DIAGNOSTIC COMPLETE ==="
echo
echo "SUMMARY AND RECOMMENDATIONS:"
echo

# Summary logic
DOCKER_EXECUTABLE=false
DOCKER_DAEMON=false
DOCKER_PERMISSIONS=false

if command -v docker >/dev/null 2>&1; then
    DOCKER_EXECUTABLE=true
fi

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    DOCKER_DAEMON=true
fi

if groups | grep -q docker; then
    DOCKER_PERMISSIONS=true
fi

echo "Status Summary:"
echo "- Docker Executable: $DOCKER_EXECUTABLE"
echo "- Docker Daemon: $DOCKER_DAEMON"  
echo "- Docker Permissions: $DOCKER_PERMISSIONS"
echo

if [ "$DOCKER_EXECUTABLE" = true ] && [ "$DOCKER_DAEMON" = true ] && [ "$DOCKER_PERMISSIONS" = true ]; then
    echo "🎉 DOCKER IS FULLY FUNCTIONAL!"
    echo "Your Jenkins pipeline should be able to use Docker."
elif [ "$DOCKER_EXECUTABLE" = true ] && [ "$DOCKER_DAEMON" = true ] && [ "$DOCKER_PERMISSIONS" = false ]; then
    echo "⚠️  DOCKER WORKS BUT PERMISSIONS ISSUE"
    echo "SOLUTION: Add Jenkins user to docker group:"
    echo "  sudo usermod -aG docker $(whoami)"
    echo "  sudo systemctl restart jenkins"
elif [ "$DOCKER_EXECUTABLE" = true ] && [ "$DOCKER_DAEMON" = false ]; then
    echo "⚠️  DOCKER INSTALLED BUT DAEMON NOT RUNNING"
    echo "SOLUTIONS:"
    echo "  sudo systemctl start docker"
    echo "  sudo systemctl enable docker"
elif [ "$DOCKER_EXECUTABLE" = false ]; then
    echo "❌ DOCKER NOT INSTALLED OR NOT IN PATH"
    echo "SOLUTIONS:"
    echo "  # Ubuntu/Debian:"
    echo "  sudo apt update && sudo apt install docker.io"
    echo "  # CentOS/RHEL:"
    echo "  sudo yum install docker"
    echo "  # Or install Docker CE from official repo"
else
    echo "❌ MULTIPLE DOCKER ISSUES DETECTED"
    echo "Review the diagnostic output above for specific problems"
fi

echo
echo "Next steps:"
echo "1. Run this script on your Jenkins server"
echo "2. Apply the recommended solutions"
echo "3. Re-run your Jenkins pipeline"
echo "4. Docker stages should now work!"
// Temporary Jenkins stage to diagnose Docker availability
// Add this stage to your Jenkinsfile after the "Environment Check & Setup" stage

    stage('Docker Diagnostic') {
      steps {
        script {
          echo "=== JENKINS DOCKER DIAGNOSTIC ==="
          
          sh '''
            echo "1. Current user and environment:"
            echo "User: $(whoami)"
            echo "Home: $HOME"
            echo "PATH: $PATH"
            echo
            
            echo "2. Searching for Docker executable:"
            for location in /usr/bin/docker /usr/local/bin/docker /bin/docker /snap/bin/docker; do
              echo "  Checking: $location"
              if [ -x "$location" ]; then
                echo "    ✅ Found and executable"
                echo "    Version: $($location --version)"
              else
                echo "    ❌ Not found or not executable"
              fi
            done
            echo
            
            echo "3. Command availability test:"
            if command -v docker >/dev/null 2>&1; then
              echo "✅ Docker found via command -v: $(command -v docker)"
              echo "Version: $(docker --version)"
            else
              echo "❌ Docker not found via command -v"
            fi
            echo
            
            echo "4. Docker daemon test:"
            if command -v docker >/dev/null 2>&1; then
              if docker info >/dev/null 2>&1; then
                echo "✅ Docker daemon accessible"
                docker system info | head -5
              else
                echo "❌ Docker daemon not accessible"
                echo "Error:"
                docker info 2>&1 | head -3
              fi
            else
              echo "❌ Cannot test daemon - docker command not available"
            fi
            echo
            
            echo "5. User permissions:"
            echo "Groups: $(groups)"
            if groups | grep -q docker; then
              echo "✅ User is in docker group"
            else
              echo "❌ User is NOT in docker group"
            fi
            echo
            
            echo "6. Docker socket:"
            if [ -S /var/run/docker.sock ]; then
              echo "✅ Docker socket exists"
              ls -la /var/run/docker.sock
            else
              echo "❌ Docker socket not found"
            fi
            echo
            
            echo "7. Docker processes:"
            ps aux | grep docker | grep -v grep | head -3 || echo "No Docker processes found"
            echo
            
            echo "8. Package check:"
            if command -v dpkg >/dev/null 2>&1; then
              dpkg -l | grep docker | head -3 || echo "No Docker packages found"
            else
              echo "dpkg not available"
            fi
          '''
        }
      }
    }